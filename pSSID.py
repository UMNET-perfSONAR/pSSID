from parse_config import Parse, tests
from schedule import Schedule
import argparse
import daemon
import sys
import time
import datetime
import rest_api
import psjson
import os
import signal
import ssid_scan
import connect_bssid
import json
import warnings
import pika
import psutil


parser = argparse.ArgumentParser(description='pSSID')
parser.add_argument('file', action='store',
  help='json file')
parser.add_argument('--debug', action='store_true',
  help='sanity check')
args = parser.parse_args()


child_exited = False
DEBUG = args.debug



def list_children():
    current_process = psutil.Process()
    children = current_process.children(recursive=True)


    if not children:
        print("NO CHILDREN")

    for child in children:
        print('Child pid is {}'.format(child.pid))




def sigh(signum, frame):
    global child_exited
    global DEBUG
    if signum == signal.SIGTERM:
        exit(1)

    if signum == signal.SIGCHLD:
        (pid, status) = os.waitpid(-1, 0)
        child_exited = True
        if DEBUG:
            print ("(SIGCHLD) child exited with status: " + str(os.WEXITSTATUS(status)), pid)
            print("PARENT CHILD: %d %d"% (os.getpid(), pid))


def print_bssid(diagnostic, bssid):
    print
    print(diagnostic)
    print(bssid)


def is_rogue(bssid, ssid_list):
    rogue_ssid = True
    ssid = None

    for i in ssid_list:
        # for scan check if matches any other ssid
        if bssid["ssid"] == i["SSID"]:
            rogue_ssid = False
            ssid = i
            break

    return rogue_ssid, ssid


def channel_match(bssid, ssid):
    if bssid["channel"] not in ssid["channels"]:
        return False
    return True



def scan_qualify(bssid_list, ssid_list, unknown_SSID_warning):
    global DEBUG

    rogue_list = []
    qualified_per_ssid = {}
    return_obj = []


    for i in ssid_list:
        qualified_per_ssid[i["SSID"]] = 0

    for bssid in bssid_list:
        bssid = json.loads(bssid)
        checked_bssid = {}
        checked_bssid["BSSID"] = bssid
        checked_bssid["rogue_ssid"] = False
        checked_bssid["channel_mismatch"] = False

        rogue, ret_ssid = is_rogue(bssid, ssid_list)

        if rogue:
            checked_bssid["rogue_ssid"] = True

            if bssid['ssid'] not in rogue_list:
                rogue_list.append(bssid['ssid'])

                if unknown_SSID_warning:
                    diagn = "Rogue SSID: " + bssid['ssid']
                    #print(diagn, bssid)
        elif not channel_match(bssid, ret_ssid):
            checked_bssid["channel_mismatch"] = True
            if ret_ssid["channel_mismatch_warning"]:
                diagn = "channel mismatch: for SSID " + ret_ssid["SSID"] + " " + str(ret_ssid["channels"])
                #print(diagn, bssid)
        elif bssid["signal"] >= ret_ssid["min_signal"]:
            qualified_per_ssid[ret_ssid["SSID"]] += 1

        return_obj.append(checked_bssid)


    for j in ssid_list:
        if qualified_per_ssid[j["SSID"]] < j["min_qualifying"]:
            if DEBUG: print("Too few qualified_bssids for", j["SSID"])


    return return_obj, qualified_per_ssid





def single_BSSID_qualify(bssid, ssid):
    """
    Take in a json object representing a bssid
    Return True if criteria is met

    ssid is a single SSID_profiles object
    """
    ret = True

    if bssid["ssid"] != ssid["SSID"]:
            return False

    # Disqualify based on channel
    if not channel_match(bssid, ssid):
        if not ssid["channel_mismatch_connect"]:
            ret = False

    # Disqualify based on signal strength
    if bssid["signal"] < ssid["min_signal"]:
        ret = False



    return ret






def BSSID_qualify(bssid_list, ssid):
    """
    Take in a list of all bssids
    Returns the number of valid bssids according to the input values

    ssid is a single SSID_profiles object
    """
    qualified_bssids = 0


    for bssid in bssid_list:
        bssid = json.loads(bssid)
        if single_BSSID_qualify(bssid, ssid):
            qualified_bssids += 1



    return qualified_bssids



def transform(main_obj, bssid):
    transform = {}
    transform["SSID"] = bssid["ssid"]
    transform["BSSID"] = bssid["address"]
    transform["ESSID"] = bssid["ssid"]
    transform["task"] = main_obj["name"]
    transform["signal"] = bssid["signal"]
    transform["frequency"] = bssid["frequency"]
    transform["meta"] = main_obj["meta"]


    #for syslog:
    script_str = psjson.json_dump(transform)
    insert = ", \\(.)"
    script_str = script_str.replace("\"", "\\\"")
    script_str = script_str.rstrip("}")
    script_str ="\""+ script_str + insert + "}\""

    append = "\"\\\"test\\\": \\\"\\(.test.type)\\\", \\\"succeeded\\\": \\(.result.succeeded), \" + if (.result.succeeded) then \"\\\"result\\\": \\(.result)\" else \"\\\"error\\\":\\\"err\\\"\" end | "

    #list
    archives_list = main_obj["TASK"]["archives"]
    new_list = []
    for i in archives_list:

        i["transform"] = {}
        if i["archiver"] == "rabbitmq":
            i["transform"]["script"] = '.pSSID = '  + json.dumps(transform)
        else:    
            i["transform"]["script"] = append + script_str #tested and works with syslog
        

        new_list.append(i)
        #print(i)

    #print(script_str)

    return new_list


def debug(parsed_file, schedule):
    #print parsed objects
    tests(parsed_file)
    schedule.print_queue()


def retrieve(next_task):
    return next_task.argument[0], \
        next_task.argument[1], \
        next_task.argument[2], \
        next_task.argument[3]


def rabbitmqQueue(message, queue_name ="", routing_key = "", exchange_name = ""):
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel=connection.channel()
    result=channel.queue_declare(queue=queue_name)
    channel.basic_publish(exchange=exchange_name, routing_key=routing_key, body=message)
    connection.close()


# read config file
# call function in parse_config.py
# parse_config.py sub-main will validate that the config file is correct
config_file = open(args.file, "r")
parsed_file = Parse(config_file)
config_file.close()



schedule = Schedule(parsed_file)
schedule.initial_schedule()




def loop_forever():
   
    global child_exited
    global DEBUG
    pid_child = 0
    connect_ttl = 20
    task_ttl = 0
    computed_TTL = 0


    interface = {}
    scanned_table = []
    bssid_list = {}

    next_task = schedule.get_queue[0]
    schedule.pop(next_task)
    main_obj, cron, ssid, scan = retrieve(next_task)

    if DEBUG:
        print("Next Task: ")
        print_task = time.ctime(next_task.time) + \
            " main_obj: " + main_obj["name"]
        print (print_task)


    old_sig = signal.signal(signal.SIGCHLD, sigh)
    while True:

        if scan:

            if next_task.time > time.time():
                sleep_time = next_task.time - time.time()
                if DEBUG: print("Waiting: ", sleep_time)
                time.sleep(sleep_time)


            ssid_list = main_obj["profiles"]



            scanned_table = ssid_scan.get_all_bssids(main_obj["interface"])

            checked_bssid, qualified_per_ssid = scan_qualify(scanned_table, ssid_list, main_obj["unknown_SSID_warning"])


            bssid_list["meta"] = main_obj["meta"]
            bssid_list["operation"] = "scan"
            bssid_list["SSID_bad_coverage"] = []

            for j in ssid_list:
                if qualified_per_ssid[j["SSID"]] < j["min_qualifying"]:
                    obj = {}
                    obj["SSID"] = j["SSID"]
                    obj["min_qualifying_BSSID"] = j["min_qualifying"]
                    obj["min_signal"] = j["min_signal"]
                    obj["qualified_BSSIDs"] = qualified_per_ssid[j["SSID"]]
                    bssid_list["SSID_bad_coverage"].append(obj)


            bssid_list[main_obj["name"]] = checked_bssid
            interface[main_obj["name"]] = main_obj["interface"]
            message = json.dumps(bssid_list)

            rabbitmqQueue(message, "pSSID", "pSSID")

            schedule.reschedule(main_obj,cron, ssid, scan=True)


            next_task = schedule.get_queue[0]
            schedule.pop(next_task)
            main_obj, cron, ssid, scan = retrieve(next_task)

            if DEBUG:
                print("Next Task: ")
                print_task = time.ctime(next_task.time) + \
                    " main_obj: " + main_obj["name"]
                print (print_task)

            child_exited = False
            continue

        if pid_child != 0:
            waittime = time.time() + computed_TTL
            while not child_exited and time.time() < waittime:
                continue

        elif next_task.time > time.time():
            sleep_time = next_task.time - time.time()
            if DEBUG: print("Waiting: ", sleep_time)
            time.sleep(sleep_time)




        if(pid_child != 0):
            if not child_exited:
                if DEBUG: print ("***kill child***", pid_child)
                os.kill(pid_child, signal.SIGKILL)
                try:
                    os.wait()
                except:
                    if args.debug: print("CHILD DEAD")
            else:
                child_exited = False

            pid_child = 0
            schedule.reschedule(main_obj, cron, ssid)
            if DEBUG:
                print("NEW QUEUE:")
                schedule.print_queue()

            next_task = schedule.get_queue[0]
            schedule.pop(next_task)
            main_obj, cron, ssid, scan = retrieve(next_task)

            if schedule.empty():
                print("ERROR: this should never reach")

            continue


        task_ttl = main_obj["ttl"] + connect_ttl
        num_bssids = BSSID_qualify(scanned_table, ssid)

        #Compute task time to live
        if num_bssids:
            computed_TTL = num_bssids * task_ttl
            if DEBUG: print("TTL", computed_TTL, num_bssids)
        else:
            schedule.reschedule(main_obj, cron, ssid)
            if DEBUG:
                print("NEW QUEUE:")
                schedule.print_queue()

            next_task = schedule.get_queue[0]
            schedule.pop(next_task)
            main_obj, cron, ssid, scan = retrieve(next_task)
            continue



        pid_child = os.fork()

        if pid_child == 0:

            signal.signal(signal.SIGCHLD, old_sig)
            if DEBUG: print("CHILD")

            for item in bssid_list[main_obj["BSSIDs"]]:
                bssid = item["BSSID"]
                if single_BSSID_qualify(bssid, ssid):
                    if DEBUG: print("Connect")
                    # Connect to bssid
                    connection_info = connect_bssid.prepare_connection(bssid['ssid'], bssid['address'], interface[main_obj["BSSIDs"]], ssid["AuthMethod"])
                    connection_info["bssid_info"] = bssid
                    connection_info["meta"] = main_obj["meta"]

                    connection_string = json.dumps(connection_info)
                    rabbitmqQueue(connection_string, "pSSID", "pSSID")
                    

                    #if connection fails, it won't run any test
                    if not connection_info["connected"]:
                        if DEBUG: print("Connection Failed")
                        continue

                    if "dest" not in main_obj["TASK"]["test"]["spec"].keys():
                        main_obj["TASK"]["test"]["spec"]["dest"] = connection_info["new_ip"]

                    main_obj["TASK"]["archives"] = transform(main_obj, bssid)
                    pSched_task = main_obj["TASK"]

                    rest_api.main(pSched_task)
            exit(0)






with daemon.DaemonContext(stdout=sys.stdout, stderr=sys.stderr, working_directory=os.getcwd()):
    if DEBUG:
        debug(parsed_file, schedule)
    
    loop_forever()