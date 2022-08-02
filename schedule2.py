#!/usr/bin/env python3
from crontab import CronTab
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
		processor = pscheduler.batchprocessor.BatchProcessor(batch)
		result = processor()
		cells = result["jobs"][0]["results"][0]["runs"][0]["application/json"]["ssid_list"]
		
		if not result["jobs"][0]["results"][0]["runs"][0]["application/json"]["succeeded"]:
			print("Scan failed, retrying")
			processor = pscheduler.batchprocessor.BatchProcessor(batch)
			result = processor()
			if not result["jobs"][0]["results"][0]["runs"][0]["application/json"]["succeeded"]:
				print("Scan failed again, skipping")
				return
		
		cells = result["jobs"][0]["results"][0]["runs"][0]["application/json"]["ssid_list"]

		wifi_list = []
		for cell in cells:
			bssid = json.dumps(cell)
			wifi_list.append(bssid)

		end_time = time.time()
		elapsed_time = end_time - start_time
		log_msg = "Scan finished in " + str(elapsed_time)
		
		self.active_ssid_list = wifi_list
	
	def qualify_and_run_batch_jobs(self, scheduled_batch):
		if len(self.active_ssid_list) is 0:
			print("No active SSIDs")
			return
		profiles = scheduled_batch["profiles"]
		for ssid_meta in self.active_ssid_list:
			#qualify based on signal and ssid match
			if profiles.get(ssid_meta["ssid"], 101) <= ssid_meta["signal"]:
				processor = pscheduler.batchprocessor.BatchProcessor(scheduled_batch["BATCH"])
				result = processor()
				print(json.dumps(result))
				return
		

		return None


	#running a scheduled_scan or scheduled_batch
	def run_batch(self, scheduled_batch, cron, scan=False):
		print_syslog = scheduled_batch["name"]+" running at "+datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		print (print_syslog)
		
		#check if the batch is a scan or a batch
		if scan:
			self.run_scan(scheduled_batch["batch"])
		#if it is a batch, send the batch
		else:
			self.qualify_and_run_batch_jobs(scheduled_batch)
		#add the next event to the queue
		print_syslog = "rescheduled in "+str(cron.next(default_utc=True))+" seconds"
		print (print_syslog)
		#reschedules itself
		self.s.enter(int(math.ceil(cron.next(default_utc=True))), scheduled_batch["priority"], self.run_batch, argument=(scheduled_batch, cron, scan))

	
	def send_batch(self, batch):
		self.print_event(batch)
		
	def initial_schedule(self, given_time=time.time()):
		SCANS = self.p.get_scheduled_scans()
		#dry run one bssid scan
		self.run_scan(SCANS[0]["batch"])
		for each_scan in SCANS:
			cron_list = each_scan["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), each_scan["priority"], self.run_batch, argument = (each_scan, each_cron, True))

		BATCHES = self.p.get_scheduled_batches()
		for each_batch in BATCHES:
			cron_list = each_batch["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), each_batch["priority"], self.run_batch, argument=(each_batch, each_cron))

		
	def print_queue(self):
		for i in self.s.queue:
			self.print_event(event=i)
def run_s(batch):
	"""
	Scan the given interface for all bssids
	Updates active_ssid_list
	"""
	start_time = time.time()
	processor = pscheduler.batchprocessor.BatchProcessor(batch)
	result = processor()
	if not result["jobs"][0]["results"][0]["runs"][0]["application/json"]["succeeded"]:
		print("Scan failed, retrying")
		processor = pscheduler.batchprocessor.BatchProcessor(batch)
		result = processor()
		if not result["jobs"][0]["results"][0]["runs"][0]["application/json"]["succeeded"]:
			print("Scan failed again, skipping")
			return
		
	cells = result["jobs"][0]["results"][0]["runs"][0]["application/json"]["ssid_list"]

	wifi_list = []
	for cell in cells:
		bssid = json.dumps(cell)
		wifi_list.append(bssid)
	print(wifi_list)
	end_time = time.time()
	elapsed_time = end_time - start_time
	log_msg = "Scan finished in " + str(elapsed_time)



if __name__ == "__main__":
	scan_batch = {}
	scan_batch["schema"] = 2
	scan_batch["jobs"] = []
	scan_batch["jobs"].append({"label":"bssid_scan","task":{"test":{"type":"wifibssid", "spec":{"interface":"wlan0"}}}})

	run_s(scan_batch)

	
		

