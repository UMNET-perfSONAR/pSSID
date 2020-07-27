
import psjson
import traceback
from crontab import CronTab
import sys
import argparse


    #checks for scans defined and creates a dictionary of the scan objects
def scan_bssids(self):
    all_scans = {}

    for i in self.BSSID_scans:
        scan_obj = {}
        try:
            scan_profile = self.BSSID_scans[i]
            scan_obj["name"] = i
            scan_obj["interface"] = self.network_interfaces[scan_profile["interface"]]
            scan_obj["profiles"] = self.SSIDs_for_profiles(scan_profile["profiles"])

            scan_obj["unknown_SSID_warning"] = scan_profile["unknown_SSID_warning"]
            scan_obj["priority"] = scan_profile["priority"]
            
            scan_obj["meta"] = self.meta[scan_profile["meta_information"]]
        except:
            print("ERROR in retrieving \"BSSID_scans\"")
            print(traceback.print_exc())

    

        try:
            cron_list = []
            schedlist = scan_profile["schedule"]
            for j in schedlist:
                scansched = self.schedules[j]
                cron_list.append(CronTab(str(scansched["repeat"])))

            scan_obj["schedule"] = cron_list
        except:
            print("ERROR in retrieving \"schedule\" from BSSID_scans")
            print(traceback.print_exc())

        
        all_scans[i] = scan_obj

    return all_scans

#Parse:
    #extracts the individual dictionaries 
    #returns them:
        #has the option of returning any specific dictionary or all at once
    #creates and returns single task formatted for pScheduler given task info
    #creates and returns single task formatted for pSSID given task info
        #(with cron scheduler and SSID list)
    #creates and returns list of all tasks from config file formatted for pSSID
    #takes one argument: json configuration file

class Parse:

    def __init__(self, config_file):
        #psjson makes sure that it is a valid json file
        json_obj =  psjson.json_load(source=config_file)

        try:
            self.meta = json_obj["meta_information"]
            self.archives = json_obj["archives"]
            self.tests = json_obj["tests"]
            self.schedules = json_obj["schedules"]
            self.BSSID_channels = json_obj["BSSID_channels"]
            self.SSID_profiles = json_obj["SSID_profiles"]
            self.SSID_groups = json_obj["SSID_groups"]
            self.network_interfaces = json_obj["network_interfaces"]
            self.BSSID_scans = json_obj["BSSID_scans"]
            self.tasks = json_obj["tasks"]

            self.all_scans = scan_bssids(self)


        except:
            print("ERROR: Make sure all fields are present")
            print(traceback.print_exc())



    #retuens the dicts in that order, to access individual see example tests below
    def return_all(self):
        return self.meta, self.archives, \
        self.tests, self.schedules, self.tasks



    #returns cron schedule list for a given task
    def schedule_for_task(self,given_task):
        try:
            cron_list = []
            schedlist = self.tasks[given_task]["schedule"]
            for i in schedlist:
                tasksched = self.schedules[i]
                cron_list.append(CronTab(str(tasksched["repeat"])))
        except:
            print("ERROR in retrieving \"schedule\" from", given_task)
            print(traceback.print_exc())

        return cron_list




    def SSIDs_for_profiles(self,profiles):        
        try:
            ssids = [] 

            if type(profiles) is list:
                ssidlist = profiles 
            else:
                ssidlist = self.SSID_groups[profiles]

            #print("ssidlist", ssidlist)
            
            for i in ssidlist:
                ssid = self.SSID_profiles[i]
                if type(ssid["channels"]) is not list:
                    ssid["channels"] = self.BSSID_channels[ssid["channels"] ]
                ssids.append(ssid)
        except:
            print("ERROR in retrieving \"SSIDs\" from", profiles)
            print(traceback.print_exc())

        return ssids

    
   
    #option to get a pscheduler formatted for specific task
    #running this function validates every key(archives,tests, etc) also valid
    def create_pScheduler_task(self, given_task, given_test):
        #scheudle needs to be empty when sent to pScheduler
        taskobj = {
            "schema" : 1,
            "schedule": {}
        }
        #validate tests
        try:
            taskobj["test"]= self.tests[given_test]
        except:
            print("ERROR in retrieving \"test\" from", given_task, given_test)
            print(traceback.print_exc())        
        #validate archives
        try:
            taskobj["archives"] = []
            archives_list = self.tasks[given_task]["archives"]
            for i in archives_list:
                taskobj["archives"].append(self.archives[i])
        except:
            print("ERROR in retrieving \"archives\" from", given_task)
            print(traceback.print_exc())
        return taskobj


    
    # running this function validates SSIDs and schedule
    # pSSID task object. Dict keys: TASK, Sched, SSIDS
    # TASKS: contain formatted tasks for valid for pscheduler
    # Sched: list of cron schedule info
    # SSIDs: list of SSIDs associated with task
    def create_pSSID_task(self, given_task, given_test):
        taskobj = {}
        taskobj["name"] = given_test
        taskobj["TASK"] = self.create_pScheduler_task(given_task, given_test)

        #Attaching schedule
        taskobj["schedule"] = self.schedule_for_task(given_task)

        #Attaching SSIDs 
        taskobj["SSIDs"] = self.SSIDs_for_profiles(self.tasks[given_task]["profiles"])

        #interface
        taskobj["interface"] = self.all_scans[self.tasks[given_task]["BSSIDs"]]

        #TODO: priority
        taskobj["priority"] = self.tasks[given_task]["priority"]

        taskobj["BSSIDs"] = self.tasks[given_task]["BSSIDs"]

        taskobj["ttl"] = self.tasks[given_task]["ttl"]

        taskobj["meta"] = self.meta[self.tasks[given_task]["meta_information"]]

        return taskobj

    

    #option to return list of pSSID task objects. Dict keys: TASK, Sched, SSIDS
    def pSSID_task_list(self):
        TASKS = []
        for eachtask in self.tasks:
            for eachtest in self.tasks[eachtask]["test"]:
                TASKS.append(self.create_pSSID_task(eachtask, eachtest))

        return TASKS

    


def tests(p):
    #single dict test:
    #optionally use psjson.json_dump() to pretty print
    print("SINGLE")
    print("meta:", p.meta)
    print("archives:", p.archives)
    print("tests:", p.tests)
    print("schedules:", p.schedules)
    print("tasks:", p.tasks)


    print("BSSID_channels", p.BSSID_channels) 
    print("SSID_profiles", p.SSID_profiles)
    print("SSID_groups", p.SSID_groups) 
    print("newwork_interfaces", p.network_interfaces)
    print("BSSID_scans", p.BSSID_scans)

    print
    print("all_scans", p.all_scans)


    print("SINGLE END")
    print
    print
    print

    #pscheduler task
    psched = p.create_pScheduler_task("example_task_throughput", "example_test_throughput_ul")
    print(psched)
    print
    print
    print



    #pSSID task
    pssid = p.create_pSSID_task("example_task_throughput", "example_test_throughput_ul")
    print(pssid)
    print
    print
    print

    #task list
    print(p.pSSID_task_list())
    print
    print
    print

    #TODO XXX: more tests






#sub-main for testing purposes
#also serves as usage

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='pSSID')
    parser.add_argument('file', action='store',
      help='json file')
    args = parser.parse_args()


    config_file = open(args.file, "r")

    p = Parse(config_file)
    tests(p)    


    

    exit(0)

