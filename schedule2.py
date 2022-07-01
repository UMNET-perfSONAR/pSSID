#!/usr/bin/env python3
from crontab import CronTab
from datetime import date, datetime
import sched, time, math, json
import pscheduler.batchprocessor
import bssid_scan


class Schedule:

	def __init__(self, parsed_file):
		self.p = parsed_file
		self.s = sched.scheduler(time.time, time.sleep)
    
	def clear_queue(self):
		self.s = sched.scheduler(time.time, time.sleep)

	def run_scan(self, batch):
		ssid_list = batch["profiles"]

		scanned_table, scan_duration = bssid_scan.get_all_bssids(batch["BATCH"])
		print("bssid scan finished in "+str(scan_duration)+"seconds")
		# filter qualifying bssids
		self.p.checked_BSSID_list = bssid_scan.scan_qualify(scanned_table, ssid_list, True)

	def run_batch(self, batch, cron, scan=False):
		print_syslog = batch["name"]+" running at "+datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		print (print_syslog)
		
		#check if the batch is a scan or a batch
		if scan :
			self.run_scan(batch)
		#if it is a batch, send the batch
		else:
			#if empty list
			for checked_bssid in self.p.checked_BSSID_list:
				# if mismatch do we perforom a test?
				if checked_bssid["good_signal"] and not checked_bssid["rogue_ssid"]:

				

			processor = pscheduler.batchprocessor.BatchProcessor(batch["BATCH"])
			result = processor()
			print(json.dumps(result))
		#add the next event to the queue
		print_syslog = "rescheduled in "+str(cron.next(default_utc=True))+" seconds"
		print (print_syslog)
		self.s.enter(int(math.ceil(cron.next(default_utc=True))), batch["priority"], self.run_batch, argument=(batch, cron))

	def send_batch(self, batch):
		self.print_event(batch)
		
	def initial_schedule(self, given_time=time.time()):
		SCANS = self.p.all_scans
		for each_scan in SCANS.values():
			cron_list = each_scan["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), each_scan["priority"], self.run_batch, argument = (each_scan, each_cron, True))

		BATCHES = self.p.pSSID_batch_list()
		for each_batch in BATCHES:
			cron_list = each_batch["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), each_batch["priority"], self.run_batch, argument=(each_batch, each_cron))

	def print_queue(self):
		for i in self.s.queue:
			self.print_event(event=i)
	
		

