#!/usr/bin/env python3
from croniter import croniter
from datetime import date, datetime
import sched, time, math, json
import pscheduler.batchprocessor
import bssid_scan


class Schedule:

	def __init__(self, parsed_file):
		self.active_ssid_list = []
		self.p = parsed_file
		self.s = sched.scheduler(time.time, time.sleep)

    
	def clear_queue(self):
		self.s = sched.scheduler(time.time, time.sleep)
	
	
	def run_scan(self, batch):
		"""
		Scan the given interface for all bssids
		Updates active_ssid_list
		"""
		start_time = time.time()
		print("sending batch to pscheduler, awaiting result")
		processor = pscheduler.batchprocessor.BatchProcessor(batch)
		result = processor()
		print("result received")
		
		if not result["jobs"][0]["results"][0]["runs"][0]["application/json"]["succeeded"]:
			print("Scan failed, retrying")
			processor = pscheduler.batchprocessor.BatchProcessor(batch)
			result = processor()
			if not result["jobs"][0]["results"][0]["runs"][0]["application/json"]["succeeded"]:
				print("Scan failed again, skipping")
				return
		cells = result["jobs"][0]["results"][0]["runs"][0]["application/json"]["ssid_list"]
		end_time = time.time()
		elapsed_time = end_time - start_time
		print("Scan finished in " + str(elapsed_time)) 
		self.active_ssid_list = cells
	
	def qualify_and_run_batch_jobs(self, scheduled_batch):
		if len(self.active_ssid_list) is 0:
			print("No active SSIDs")
			return
		profiles = scheduled_batch["profiles"]
		for ssid_meta in self.active_ssid_list:
			#qualify based on signal and ssid match
			if profiles.get(ssid_meta["ssid"], 101) <= ssid_meta["signal"]:
				print("signal"+str(ssid_meta["signal"])+"greater than"+str(profiles.get(ssid_meta["ssid"]))+"running measurements against " + ssid_meta["address"])
				#TODO: assumption: layer 2 test is always the first test
				scheduled_batch["batch"]["jobs"][0]["task"]["reference"]["tests"][0]["spec"]["bssid"] = ssid_meta["address"]
				print(scheduled_batch["batch"])
				processor = pscheduler.batchprocessor.BatchProcessor(scheduled_batch["batch"])
				result = processor()
				print(json.dumps(result, indent=2))
				
		return None


	#running a scheduled_scan or scheduled_batch
	def run_batch(self, scheduled_batch, cron, scan=False):
		print_syslog = scheduled_batch["name"]+" running at "+datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		print (print_syslog)
		
		#check if the batch is a scan or a batch
		if scan:
			print("scanning")
			self.run_scan(scheduled_batch["batch"])
		#if it is a batch, send the batch
		else:
			print("running jobs")
			self.qualify_and_run_batch_jobs(scheduled_batch)
		#add the next event to the queue
		print_syslog = "rescheduled at "+str(cron.get_next(datetime))
		print (print_syslog)
		#reschedules itself
		self.s.enterabs(cron.get_next(datetime).timestamp(), scheduled_batch["priority"], self.run_batch, argument=(scheduled_batch, cron, scan))

	
	def send_batch(self, batch):
		self.print_event(batch)
		
	def initial_schedule(self):
		SCANS = self.p.get_scheduled_scans()
		#dry run one bssid scan
		print("start initial scanning")
		self.run_scan(SCANS[0]["batch"])
		print("initial scanning finished")
		for each_scan in SCANS:
			cron_list = each_scan["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(each_cron.get_next(datetime).timestamp(), each_scan["priority"], self.run_batch, argument = (each_scan, each_cron, True))

		BATCHES = self.p.get_scheduled_batches()
		for each_batch in BATCHES:
			cron_list = each_batch["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(each_cron.get_next(datetime).timestamp(), each_batch["priority"], self.run_batch, argument=(each_batch, each_cron))

		
	def print_queue(self):
		for i in self.s.queue:
			self.print_event(event=i)



if __name__ == "__main__":
	scan_batch = {}
	scan_batch["schema"] = 2
	scan_batch["jobs"] = []
	scan_batch["jobs"].append({"label":"bssid_scan","task":{"test":{"type":"wifibssid", "spec":{"interface":"wlan0"}}}})