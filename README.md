# pSSID install instructions and usage

**Quick Start**:

**pSSID install**:
To install pSSID, visit [ansible-playbook-pSSID](https://github.com/UMNET-perfSONAR/ansible-playbook-pSSID) and follow the instructions.

**pSSID Usage**:

cd into the directory where pSSID is installed:

```
cd /<path>/pssid
```

To run the daemon, use:

```
python3 pSSID.py pSSID_skeleton.json
```
This will run the tests and archive the results to the archivers defined in the task spec in the pSSID_skeleton.json config file


Optionally, --debug flag can be added to print parsed data from config file, schedule, and other diagnostic information to stdout:

```
python3 pSSID.py pSSID_skeleton.json --debug
```


To validate the config file without running daemon, run parse_config.py:

```
python3 parse_config.py pSSID_skeleton.json
```
This will print our parsed dictionary objects, and show if any error occured.



To see the schedule without running the daemon, run schedule.py:

```
python3 schedule.py pSSID_skeleton.json
```
This will print the first scheduled item for each task and SSID combination starting from current time 


Optionally, schedule.py takes two flags [--start YYYY-MM-DD-HH-MIN] and [--duration seconds].

Given --start, it will print out the first scheduled item for each task and SSID combination starting from start time

```
python3 schedule.py pSSID_skeleton.json --start YYYY-MM-DD-HH-MIN
```

Given --duration, which takes an argument in seconds, it will print out the whole schedule for that duration either starting from current time or --start time.

```
python3 schedule.py pSSID_skeleton.json --duration 3600
```
This will print out the schedule for an hour starting from current time.



To change the schedule,test specs, meta, etc, edit pSSID_skeleton.json accordingly. 
	-Arbitrary information can be added to probe_stats object defined inside meta_information. 
	-Default archivers used are syslog and rabbitmq. Archivers supported by pscheduler can also be added.
	-"tests" object includes pscheduler formatted test. Any tests supported by pscheduler and formatted correctly can be added.
	-any valid cron style objects can be added to the "schedules" object and referenced in the test spec
	-Default SSID profiles are MWireless and Eduroam. New SSID profiles can be added to SSID_profiles object. Make sure to keep all the fields and names consistent. Use MWireless and Eduroam as example.
	-"BSSID_scans" and "tasks" are two main objects that reference the previously defined objects and tell pSSID how to run a test. Edit the fields if necessary and make sure that it is a valid reference to a defined object. Do not remove any fields.




