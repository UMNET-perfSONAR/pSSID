# Connecting to WiFi using WPA

pSSID uses wpa to connect to wifi. For each SSID there is a file named `wpa_supplicant_[SSID].conf` in the directory `/etc/wpa_supplicant/` that stores information necessary to connect to that particualr SSID.

The wpa config  file is created during pssid install time. This [playbook](https://github.com/UMNET-perfSONAR/ansible-inventory-pssid-ilab/blob/master/playbooks/dhcp_network.yml) creates a file for every SSID defined in the inventory. It temporarily uses placeholder for password which needs to be edited with the correct password by changing the password field for SSIDs defined in the inventory. The [configure.md](https://github.com/UMNET-perfSONAR/pSSID/blob/master/configure.md) file has instructions on how to manually set up wpa. There's also [troubleshoot.md](https://github.com/UMNET-perfSONAR/pSSID/blob/master/troubleshoot.md) that has instructions how to troubleshoot network issues among other pssid issues.

The wpa files are used by [connect_bssid.py](https://github.com/UMNET-perfSONAR/pSSID/blob/master/connect_bssid.py). This file replaces the bssid field in the wpa config file and then connects to that particular bssid. 

Below is an example of how to test connection. These commands will work after installing pssid in a probe and navigating to `/usr/local/bin/pssid`\
Commands to connect to MWireless through cli using [connect_bssid.py](https://github.com/UMNET-perfSONAR/pSSID/blob/master/connect_bssid.py):

```
python3 connect_bssid.py [ssid] [bssid] [interface_name]
python3 connect_bssid.py MWireless [bssid] wlan0
```

Commands to scan for bssids for MWireless:
```
python3 ssid_scan.py wlan0 MWireless
```
If the scan does not return any result, make sure that wlan0 is up:
```
ip link set wlan0 up
```

