# pSSID Troubleshooting Guide

This a guide to debugging pSSID parser, scheduler, config file, and REST API script, and troubleshooting network issues, pScheduler, elastic search, and rabbitmq.

**pSSID files and sub-mains:**


* Parse config file:
To validate the config file without running daemon, run parse_config.py:
```
python3 parse_config.py pSSID_skeleton.json
```
This will print our parsed dictionary objects, and show if any error occurred


* View Schedule:
To see the schedule without running the daemon, run schedule.py:
```
python3 schedule.py pSSID_skeleton.json
```
This will print the first scheduled item for each task and SSID combination starting from current time 

Optionally, schedule.py takes two flags [--start YYYY-MM-DD-HH-MIN] and [--duration *seconds*].

Given --start, it will print out the first scheduled item for each task and SSID combination starting from start time
```
python3 schedule.py pSSID_skeleton.json --start YYYY-MM-DD-HH-MIN
```
Given --duration, which takes an argument in seconds, it will print out the whole schedule for that duration either starting from current time or --start time.
```
python3 schedule.py pSSID_skeleton.json --duration 3600
```
This will print out the schedule for an hour starting from current time.


* Test the REST API:
To test if REST API is working properly, run:
```
python3 rest_api.py 
```
It will run a default pScehduler test. To see the output in stdout use -o flag. To see the output in syslog, use -s flag. There is also -q to flag, to send the results to pScheduler rabbitmq but edit the url and routing-key appropriately.

* Test connection:
```
python3 connect_bssid.py ssid bssid interface_name
```

* Test scan:
```
python3 ssid_scan.py interface_name ssid
```

**Network Issues**

Manually test scanning:
```
iwlist wlan0 s
```

This will return objects for all bssids
If it does not the interface may be down
```
ip link set wlan0 up
```

**pScheduler Troubleshooting**
```
pscheduler Troubleshoot:
pscheduler ping ip_wireless_interface
pscheduler ping ip_wired_interface
```

Should come back quickly saying pscheduler is alive

**Machine configurations:**

	* Elastic machine:
		/etc/logstash/second.conf config file for second pipeline add all the Pis in input 
		/var/log/messages useful log file other logs can be found in program specific directories(rabbitmq, logstash, elasticsearch)
		Selinux should be off
		Firewalld should be off
		Ports 5601 9200 5672 should be opened
		Last commands in elastic role(xpack) enable kibana alerting if they dont work comment them out
	* PSSIDs: 
		rabbitmqctl list_users  make sure u have hi user if not 
		rabbitmqctl add_user hi hi
		rabbitmqctl set_permissions -p / hi “.*” “.*” “.*”
                     systemctl status rabbitmq-server check if rabbitmq is running 	     
                 cd /var/log/rabbitmq/ look into log files in case something isnt working
		systemctl status firewalld Firewall should be off if not
  		systemctl stop firewalld
		

