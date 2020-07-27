import rest_api
import datetime
import json
import time
import traceback
import daemon
import sys
import sched
from parse_config import Parse
import syslog
import argparse

count = 0


def run_schedule(obj, cron, ssid, scan):
	global count
	count += 1
	print
	print("Main reached", count)
	print ("NOW: %s" % time.ctime(time.time()))
	print ("TASK: ", str(obj["name"]))
	if not scan:
		print ("SSID: ", str(ssid["name"]))
		print ("Result URL: ")
		rest_api.main(obj["TASK"])

	print




class Schedule:

	def __init__(self, parsed_file):
		self.p = parsed_file
		self.s = sched.scheduler(time.time, time.sleep)


	

	
	def reschedule(self,given_obj, given_cron, given_ssid = {}, given_time=time.time(), scan = False):
		set_time = time.time()
		if given_time > time.time():
			set_time = given_time
		
		name = given_obj["name"]
		schedule_time =  set_time  + given_cron.next(set_time)

		self.s.enterabs(schedule_time, given_obj["priority"], run_schedule, argument = (given_obj,given_cron,given_ssid, scan))




	#schedules for all tasks at the start
	def initial_schedule(self, given_time=time.time()):
		SCANS = self.p.all_scans	#SCANS is a dict
		for eachscan in SCANS.values():
			cron_list = eachscan["schedule"]
			for eachcron in cron_list:
				self.s.enterabs(time.time(), eachscan["priority"], run_schedule, argument = (eachscan, eachcron, {}, True))

		
		TASKS = self.p.pSSID_task_list()
		for eachtask in TASKS:
			cron_list = eachtask["schedule"]
			ssid_list = eachtask["SSIDs"]

			for eachssid in ssid_list:
				for eachcron in cron_list:
					self.reschedule(eachtask, eachcron, eachssid, given_time)

		self.s.queue
    	
	
	def print_event(self, event, prefix=""):
		if not event.argument[3]:
			print_syslog = prefix + time.ctime(event.time) + \
				" SSID: " + event.argument[2]["SSID"] + \
				" Test: " + event.argument[0]["name"]
		else:
			print_syslog = prefix + time.ctime(event.time) + \
				" Test: " + event.argument[0]["name"]

		print (print_syslog)


	
	def print_queue(self):
		for i in self.s.queue:
			self.print_event(event=i)


	def initial_print(self, given_time=time.time()):
		#print self.s.queue
		print ("Now: %s" % time.ctime(time.time()))
		print ("start: %s" % time.ctime(given_time))
		

		#the next scheduled run for unique task/ssid comb
		temp = {}
		for i in self.s.queue:
			if i.argument[0]["name"] not in temp:
				temp[i.argument[0]["name"]] = []
				if not i.argument[3]:
					temp[i.argument[0]["name"]].append(i.argument[2]["SSID"])
				self.print_event(i, "First: ")
			elif not i.argument[3] and i.argument[2]["SSID"] not in temp[i.argument[0]["name"]]:
				temp[i.argument[0]["name"]].append(i.argument[2]["SSID"])
				self.print_event(i, "First: ")

	


	def duration_print(self, given_time, duration):
		#both need to be in seconds
		end_time = given_time + duration

		#create a custom dict where each task has additional
		#attribut 'prev', previously scheduled time

		temp2 = []
		for i in self.s.queue:
				test = {}
				test["i"] = i
				test["prev"] = i.time
				temp2.append(test)

		
		#treat temp2 i.time as prev		
		fake_time = 0
		print("ENDTIME: ", time.ctime(end_time))
		while fake_time < end_time:
			min_time = end_time
			for test in temp2:

				curr_time = test["prev"] + test["i"].argument[1].next(test["prev"])
				test["prev"] = curr_time
				min_time = min(min_time, curr_time)

				if curr_time <= end_time:
					self.s.enterabs(curr_time, test["i"].argument[0]["priority"], run_schedule, argument = test["i"].argument)
			
			fake_time = min_time


		#print
		temp = {}
		for i in self.s.queue:
			if i.time < end_time:
				if i.argument[0]["name"] not in temp:
					temp[i.argument[0]["name"]] = []
					if not i.argument[3]:
						temp[i.argument[0]["name"]].append(i.argument[2]["SSID"])
					self.print_event(i, "First: ")
				elif not i.argument[3] and i.argument[2]["SSID"] not in temp[i.argument[0]["name"]]:
					temp[i.argument[0]["name"]].append(i.argument[2]["SSID"])
					self.print_event(i, "First: ")
				else:
					self.print_event(i, "Next: ")

	
	@property
	def get_queue(self):
		return self.s.queue

	
	def empty(self):
		return self.s.empty()

	def pop(self, event):
		self.s.cancel(event)


	def run(self):
		print("RUN")
		self.s.run()

		


def time_input_error():
	print ("please provide a valid time: \
			\"[yyyy-mm-dd-hh-min]\" ")



def main():
	#add more options to duration
	# -hours
	# -secs

	#start time

	parser = argparse.ArgumentParser(description='output options')
	parser.add_argument('file', action='store',
	  help='json file')
	parser.add_argument('--start', action='store',
	  help='start time YYYY-MM-DD-HH-MIN')
	parser.add_argument('--duration', action='store',
	  help='duration/timelength in seconds', type=int)

	args = parser.parse_args()


	

	if(args.duration == None):
		duration = 3600 #default 1 hour for now
	else:
		duration= args.duration #assuming entered as seconds
	

	if(args.start == None):
		start = time.time()
	else:
		#check for valid time range and parse it
		start_time = args.start

		
		try:
			#all strings	
			year = (start_time.split("-")[0]).lstrip().rstrip()
			month = (start_time.split("-")[1]).lstrip().rstrip()
			day = (start_time.split("-")[2]).lstrip().rstrip()
			hour = (start_time.split("-")[3]).lstrip().rstrip()
			minute = (start_time.split("-")[4]).lstrip().rstrip()
		except:
			time_input_error()
			print(traceback.print_exc())
			exit(1)
		
		
		
		start_str = year+" "+month+" "+day+" "+hour+" "+minute

		try:
			start = time.strptime(start_str, "%Y %m %d %H %M")
			start = time.mktime(start)
			print("start", time.ctime(start))
		except:
			time_input_error()
			print(traceback.print_exc())
			exit(1)

		time_given = True




	config_file = open(args.file, "r")
	p = Parse(config_file)
	s = Schedule(p)
	s.initial_schedule(start)

	if(args.duration == None):
		s.initial_print(start)
	else:
		s.duration_print(start, duration)
		
	
	s.run()

	exit(0)


if __name__ == '__main__':
	main()


