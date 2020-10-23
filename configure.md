# pSSID Configuration Guide

**Edit Configuration File**

* To change the schedule, test specs, meta, etc, edit pSSID_skeleton.json accordingly:

  Add Meta information
  - Arbitrary information can be added to probe_stats object defined inside meta_information. 
  
  Add Archives
  - Default archivers used are syslog and rabbitmq. Archivers supported by pscheduler can also be added.
  
  Add tests
  - "tests" object includes pscheduler formatted test. Any tests supported by pscheduler and formatted correctly can be added.
  
  Add new scheduler
  - Any valid cron style objects can be added to the "schedules" object and referenced in the test spec
  
  Configure SSIDS
  - Default SSID profiles are MWireless and Eduroam. New SSID profiles can be added to SSID_profiles object. Make sure to keep all the fields and names consistent. Use MWireless and Eduroam as example.
  
  Configure Scans and Tasks
  - "BSSID_scans" and "tasks" are two main objects that reference the previously defined objects and tell pSSID how to run a test. Edit the fields if necessary and make sure that it is a valid reference to a defined object. Do not remove any fields.


**Set up wpa_supplicant**

pSSID uses wpa_supplicant to connect to wireless
There are different wpa_supplicant files for each ssid

These files are stored in /etc/wpa_supplicant/
In the format wpa_supplicant_ssid.conf
Copy over template file into format wpa_supplicant_SSID.conf
```
cp /etc/wpa_supplicant/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant_ssid.conf
```

Edit new configuration file with login info
Template has slots for identity and password
If your wifi doesn't require a username, then remove the identity field

**Hash password in wpa_supplicant**
```
vi password
iconv -t utf16le < password | openssl md4
```

This password can replace password field in wpa_supplicant with the hash prefix
```
password=hash:hashed_password
```

**pScheduler command to sure up wired interface**
```
/usr/lib/perfsonar/scripts/mod_interface_route --command add --device eth0 --ipv4_gateway 198.111.224.145
```

**Routing**

When the pi comes up the wired interface will have the default route
This should be removed by the connect_bssid code
It will then bring up a default route over the wireless interface for testing

There should be routes to the gateway for the bastion and the ELK Server

Static routes can be added in the netplan yaml file
```
/etc/netplan/50-cloud-init.yaml
```

Or manually using ip route add



