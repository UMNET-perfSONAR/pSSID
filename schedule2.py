#!/usr/bin/env python3
from crontab import CronTab
from datetime import date, datetime
import sched, time, math, json
import pscheduler.batchprocessor



class Schedule:

	def __init__(self, parsed_file):
		self.p = parsed_file
		self.s = sched.scheduler(time.time, time.sleep)
    	
	def print_batch(self, batch, cron):
		print_syslog = batch["name"]+" running at "+datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		print (print_syslog)
		#sending batch to pscheduler
		
		processor = pscheduler.batchprocessor.BatchProcessor(batch["BATCH"])
		result = processor()
		print(result)
		print_syslog = "rescheduled in "+str(cron.next(default_utc=True))+" seconds"
		print (print_syslog)
		self.s.enter(int(math.ceil(cron.next(default_utc=True))), batch["priority"], self.print_batch, argument=(batch, cron))

	def send_batch(self, batch):
		self.print_event(batch)
    
	def initial_schedule(self, given_time=time.time()):
		SCANS = self.p.all_scans
		for each_scan in SCANS.values():
			cron_list = each_scan["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), each_scan["priority"], self.print_batch, argument = (each_scan, each_cron))

		BATCHES = self.p.pSSID_batch_list()
		for each_batch in BATCHES:
			cron_list = each_batch["schedule"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), each_batch["priority"], self.print_batch, argument=(each_batch, each_cron))

	def print_queue(self):
		for i in self.s.queue:
			self.print_event(event=i)

