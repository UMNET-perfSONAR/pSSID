
import psjson
import traceback
from croniter import croniter
from datetime import datetime
import sys
import argparse



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
            self.base = datetime.now()
            self.meta = json_obj["meta"]
            self.archives = json_obj["archiver-definitions"]
            self.tests = json_obj["test-definitions"]
            self.schedules = json_obj["schedule-definitions"]
            self.SSID_profiles = json_obj["ssid-profile-definitions"]
            self.BSSID_scans = json_obj["bssid-scan-definitions"]
            self.jobs = json_obj["job-definitions"]
            self.batches = json_obj["batch-definitions"]
            self.active_batches = json_obj["active-batches"]
            #schedule_scan object: {name, priority, schedule, batch}
            self.scheduled_scans = self.create_scheduled_scans()
            #schedule_batch object: {name, priority, schedule, batch, profiles}
            self.scheduled_batches = self.create_scheduled_batches()
        except:
            print("ERROR: Make sure all fields are present")
            print(traceback.print_exc())


    def get_scheduled_scans(self):
        return self.scheduled_scans
    def get_scheduled_batches(self):
        return self.scheduled_batches
    def get_batch(self, given_batch):
        return self.batches[given_batch]
    def get_scan(self, given_scan):
        return self.BSSID_scans[given_scan]
    
    def get_archiver(self, given_archiver):
        return self.archives[given_archiver]

    def get_ssid_profile(self, given_profile):
        return self.SSID_profiles[given_profile]
    
    def get_test(self, given_test):
        return self.tests[given_test]
    
    def get_job(self, given_job):
        return self.jobs[given_job]
    
    def create_batch_job(self, given_job):
        """
        Creates a job for the batch conf file
        """
        try:
            job_def = self.get_job(given_job)
            job_obj = {}
            job_obj["label"] = given_job
            job_obj["parallel"] = job_def["parallel"]
            job_obj["iterations"] = len(job_def["tests"])
            job_obj["task"] = {"reference":{"tests":[]}, "test":{}}
            job_obj["task-transform"] = {"script":[".test = .reference.tests[$iteration]"]}
            #TODO:support archives
            job_obj["task"]["archives"] = []
            for eachtest in job_def["tests"]:
                job_obj["task"]["reference"]["tests"].append(self.get_test(eachtest))
        except:
            print("ERROR in creating batch job")
            print(traceback.print_exc())

        return job_obj

    def assemble_batch(self, given_batch):
        """
        Creates a batch configuration file for pScheduler
        """
        try:
            batch_conf = {}
            batch_conf["schema"] = 2
            batch_conf["jobs"] = []
            for eachtest in self.batches[given_batch]["jobs"]:
                batch_conf["jobs"].append(self.create_batch_job(eachtest))
        except:
            print("ERROR in creating batch configuration file")
            print(traceback.print_exc())

        return batch_conf
    
    def assemble_scan(self, given_scan, bssid_scan_name):
        scan_batch = {}
        scan_batch["jobs"] = []
        scan_batch["jobs"].append({"label":"bssid_scan","task":{"test":{"type":"wifibssid", "spec":{"interface":given_scan["interface"]}}}})
        cron_list = []
        schedlist = given_scan["schedule"]
        for sched in schedlist:
            cron_list.append(croniter(str(self.schedules[sched]["repeat"]), self.base))
        return {"name":bssid_scan_name,"priority":given_scan["priority"],"schedule":cron_list, "batch":scan_batch}

    def create_scheduled_scans(self):
        bssid_set = set()
        all_scans = []
        for eachbatch in self.active_batches:
            for bssid in self.get_batch(eachbatch)["BSSIDs"]:
                if bssid in bssid_set:
                    continue
                bssid_set.add(bssid)
                all_scans.append(self.assemble_scan(self.BSSID_scans[bssid], bssid))
        
        return all_scans
    
    def schedule_for_batch(self,given_batch):
        """
        Returns list of cron object for a given batch
        """
        try:
            cron_list = []
            schedlist = self.batches[given_batch]["schedule"]
            for i in schedlist:
                cronline = self.schedules[i]
                cron_list.append(croniter(str(cronline["repeat"]), self.base))
        except:
            print("ERROR in retrieving \"schedule\" from", given_batch)
            print(traceback.print_exc())

        return cron_list

    def create_scheduled_batches(self):
        """
        returns a list of scheduled batches
        """
        all_scheduled_batches = []
        for given_batch in self.active_batches:
            single_batch = {}
            single_batch["name"] = given_batch
            single_batch["batch"] = self.assemble_batch(given_batch)
            single_batch["schedule"] = self.schedule_for_batch(given_batch)
            single_batch["priority"] = self.batches[given_batch]["priority"]
            #mapping ssid to min_signal
            single_batch["profiles"] = {}
            for eachprofile in self.batches[given_batch]["profiles"]:
                min_signal = self.SSID_profiles[eachprofile]["min_signal"]
                ssid = self.SSID_profiles[eachprofile]["SSID"]
                single_batch["profiles"][ssid] = min(min_signal, single_batch["profiles"].get(ssid, min_signal))
            all_scheduled_batches.append(single_batch)
        print(all_scheduled_batches)
        return all_scheduled_batches
    

def tests(p):
    #single dict test:
    #optionally use psjson.json_dump() to pretty print
    print("SINGLE")
    print("meta:", p.meta)
    print("archives:", p.archives)
    print("tests:", p.tests)
    print("schedules:", p.schedules)
    print("scheduled scans", p.scheduled_scans)
    print("active batches:", p.active_batches)
    print("scheduled batches", p.scheduled_batches)
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

