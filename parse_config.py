
import psjson
import traceback
from crontab import CronTab
import sys
import argparse


def scan_bssids(self):
    """
    Parses the scan objects defined in config file
    """

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
            scan_obj["meta"] = self.meta[scan_profile["meta-info"]]
            scan_obj["BATCH"] = {
                    "schema": 2,
                    "jobs": [
                        {
                            "label": i,
                            "task": [{
                                "test": {
                                    "type": "wifibssid",
                                    "spec": {
                                        "interface": scan_obj["interface"],
                                        "ssid":""
                                    }
                                }}
                            ],
                        } 
                    ]
            }

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




class Parse:
    """
    Takes one argument: json configuration file
    - Parses the individual dictionaries defined in config file  
    - creates and returns single task formatted for pScheduler given task info
    - creates and returns single task formatted for pSSID given task info  (with cron scheduler and SSID list)
    - creates and returns list of all tasks from config file formatted for pSSID 
    """

    def __init__(self, config_file):
        """
        Initializes dictionary object for each field in config file
        """

        # psjson makes sure that it is a valid json file
        json_obj =  psjson.json_load(source=config_file)

        try:
            self.meta = json_obj["meta-definitions"]
            self.amqp_url = json_obj["amqp_url"]
            self.archives = json_obj["archiver-definitions"]
            self.tests = json_obj["test-definitions"]
            self.schedules = json_obj["schedule-definitions"]
            self.BSSID_channels = json_obj["bssid-channel-definitions"]
            self.SSID_profiles = json_obj["ssid-profile-definitions"]
            self.SSID_groups = json_obj["ssid-group-definitions"]
            self.network_interfaces = json_obj["network-interface-definitions"]
            self.BSSID_scans = json_obj["bssid-scan-definitions"]
            self.jobs = json_obj["job-definitions"]
            self.batches = json_obj["batch-definitions"]
            self.active_batches = json_obj["batches"]
            self.all_scans = scan_bssids(self)


        except:
            print("ERROR: Make sure all fields are present")
            print(traceback.print_exc())



    
    def schedule_for_task(self,given_task):
        """
        Returns list of cron object for a given task
        """
        try:
            cron_list = []
            schedlist = self.batches[given_task]["schedule"]
            for i in schedlist:
                cronline = self.schedules[i]
                cron_list.append(CronTab(str(cronline["repeat"])))
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
            
            for i in ssidlist:
                ssid = self.SSID_profiles[i]
                if type(ssid["channels"]) is not list:
                    ssid["channels"] = self.BSSID_channels[ssid["channels"] ]
                ssids.append(ssid)
        except:
            print("ERROR in retrieving \"SSIDs\" from", profiles)
            print(traceback.print_exc())

        return ssids

    

    
   

    def create_pScheduler_task(self, given_task, given_test):
        """
        returns a pscheduler formatted for specific task
        running this function validates archives,tests
        """
        #scheudle needs to be empty when sent to pScheduler
        taskobj = {
            "schema" : 1,
            "schedule": {}
        }

        # validate tests
        try:
            taskobj["test"]= self.tests[given_test]
        except:
            print("ERROR in retrieving \"test\" from", given_task, given_test)
            print(traceback.print_exc()) 

        # validate archives
        try:
            taskobj["archives"] = []
            archives_list = self.tasks[given_task]["archives"]
            for i in archives_list:
                taskobj["archives"].append(self.archives[i])
        except:
            print("ERROR in retrieving \"archives\" from", given_task)
            print(traceback.print_exc())

        return taskobj


    
    def create_pSSID_task(self, given_task, given_test):
        """
        running this function validates SSIDs and schedule
        TASK: contains valid pScheduler tasks
        Sched: list of cron schedule info
        SSIDs: list of SSIDs associated with task
        """
        taskobj = {}
        taskobj["throughput"] = False
        taskobj["name"] = given_test
        taskobj["amqp_url"] = self.amqp_url
        taskobj["TASK"] = self.create_pScheduler_task(given_task, given_test)
        taskobj["schedule"] = self.schedule_for_task(given_task)

        # includes SSID profiles object infomartion
        taskobj["SSIDs"] = self.SSIDs_for_profiles(self.tasks[given_task]["profiles"])
        taskobj["interface"] = self.all_scans[self.tasks[given_task]["BSSIDs"]]
        taskobj["priority"] = self.tasks[given_task]["priority"]
        taskobj["BSSIDs"] = self.tasks[given_task]["BSSIDs"]
        taskobj["ttl"] = self.tasks[given_task]["ttl"]
        taskobj["meta"] = self.meta[self.tasks[given_task]["meta_information"]]

        if "throughput_threshold" in self.tasks[given_task]:
            taskobj["throughput"] = True
            taskobj["throughput_threshold"] = self.tasks[given_task]["throughput_threshold"]

        return taskobj
    
    
    def create_pScheduler_batch(self, eachbatch):

        batch_temp = {
                        "schema": 2,
                        "jobs": [
                                    {
                                        "label": "noop",
                                        "parallel": True,
                                        "backoff": "PT1S",
                                        "sync-start": True,
                                        "task": [{
                                            "test": {
                                                "type": "noop",
                                                "spec": {
                                                    "fail":0 
                                                }
                                            }}
                                        ],
                                        "continue-if": {
                                                "script": ".[0].runs[0].\"application/json\".succeeded"
                                        }
                                    },
                                    {

                                        "label": "noop",
                                        "parallel": True,
                                        "backoff": "PT1S",
                                        "sync-start": True,
                                        "task": [{
                                            "test": {
                                                "type": "noop",
                                                "spec": {
                                                    "fail":0 
                                                }
                                            }}
                                        ],
                                        "continue-if": {
                                                "script": ".[0].runs[0].\"application/json\".succeeded"
                                        }
                                    }
                        ]
                }

        job_instance = {
                "label": eachbatch,
                "parallel": True,
                "task": []
            }
        
        for job in self.batches[eachbatch]["jobs"]: 
            test_instance = {
                "test": self.tests[job]
            }
            job_instance["task"].append(test_instance) 
            
        batch_temp["jobs"].append(job_instance)
             
        return batch_temp
       
    def create_pSSID_batch(self, given_task):
        """
        running this function validates SSIDs and schedule
        TASK: contains valid pScheduler tasks
        Sched: list of cron schedule info
        SSIDs: list of SSIDs associated with task
        """
        taskobj = {}
        taskobj["name"] = given_task
        taskobj["BATCH"] = self.create_pScheduler_batch(given_task)
        taskobj["schedule"] = self.schedule_for_task(given_task)

        # includes SSID profiles object infomartion
        taskobj["priority"] = self.batches[given_task]["priority"]
        taskobj["BSSIDs"] = self.batches[given_task]["BSSIDs"]
        taskobj["ttl"] = self.batches[given_task]["ttl"]
        # taskobj["meta"] = self.meta[self.batches[given_task]["meta_information"]]

        return taskobj
    

   
    def pSSID_task_list(self):
        """
        option to return list of pSSID task objects. Dict keys: TASK, Sched, SSIDS
        """
        TASKS = []
        for eachbatch in self.active_batches:
            for eachtest in self.batches[eachbatch]["test"]:
                TASKS.append(self.create_pSSID_task(eachbatch, eachtest))

        return TASKS
    
    def pSSID_batch_list(self):
        """
        option to return list of batch objects. Dict keys: TASK, Sched, SSIDS
        """
        BATCHES = []
        for eachbatch in self.active_batches:
            BATCHES.append(self.create_pSSID_batch(eachbatch))
        return BATCHES


    


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
    print("all_scans", p.all_scans)
    print("SINGLE END")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='pSSID')
    parser.add_argument('file', action='store',
      help='json file')
    args = parser.parse_args()

    config_file = open(args.file, "r")

    p = Parse(config_file)
    tests(p)   

    exit(0)

