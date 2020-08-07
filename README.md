# pSSID install instructions and usage


**pSSID install**:
To install pSSID, visit [ansible-playbook-pSSID](https://github.com/UMNET-perfSONAR/ansible-playbook-pSSID) and follow the instructions.

**pSSID Usage**:

cd into the directory where pSSID is installed:

```
cd /usr/local/bin/pssid
```
/usr/local/bin/pssid is the default path. Edit the path in the installation files before installing if necessary.

To run the daemon, use:

```
python3 pSSID.py pSSID_skeleton.json
```
This will run the tests and archive the results to the archivers defined in the task spec in the pSSID_skeleton.json config file


Optionally, --debug flag can be added to print parsed data from config file, schedule, and other diagnostic information to stdout:

```
python3 pSSID.py pSSID_skeleton.json --debug
```

