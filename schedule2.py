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
		
		priority = batch["priority"]
		print_syslog = "rescheduled in"+str(cron.next(default_utc=True))+"seconds"
		print (print_syslog)
		self.s.enter(int(math.ceil(cron.next(default_utc=True))), priority, self.print_batch, argument=(batch, cron))

	def send_batch(self, batch):
		self.print_event(batch)
    
	def initial_schedule(self, given_time=time.time()):
		BATCHES = self.p.pSSID_batch_list()
		for each_batch in BATCHES:
			cron_list = each_batch["schedule"]
			priority = each_batch["priority"]
			for each_cron in cron_list:
				self.s.enterabs(given_time+int(math.ceil(each_cron.next(default_utc=True))), priority, self.print_batch, argument=(each_batch, each_cron))

	def print_queue(self):
		for i in self.s.queue:
			self.print_event(event=i)

