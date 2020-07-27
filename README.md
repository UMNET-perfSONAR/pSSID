# pSSID_install

**Quick Start**:

**RPi4 OS install**:
Install Ubuntu 18 64 bit version:
https://ubuntu.com/download/raspberry-pi
Install on SD Card as per Ubuntu's instructions.

from console:
log on as ubuntu
change user ubuntu and root password

```
sudo -s
passwd
```

**pSSID Bootstrap**:

From bastion:
Clone the playbook:

```
git clone https://github.com/UMNET-perfSONAR/ansible-playbook-pSSID.git
cd ansible-playbook-pSSID
```

Clone this inventory in the playbook dir:
```
git clone https://github.com/UMNET-perfSONAR/ansible-inventory-pssid-template.git
```

Get the required roles (ignore errors so we can run this multiple times):

```
ansible-galaxy install -r requirements.yml --ignore-errors
ansible-galaxy install \
  -r ansible-inventory-pssid-template/requirements.yml\
  --ignore-errors
```

Define testpoints, add ip address of the testpoint under [pSSID-testpoints]:

```
cd ansible-inventory-pssid-template/inventory/host_vars
vi hosts
```

clean out .ssh/known_hosts
ssh to ip defined in pSSID-testpoints

```
ansible pSSID-testpoints \
  -u ubuntu --ask-pass --become-method sudo \
  -i ansible-inventory-pssid-template/inventory \
  -m ping
```

become root
clean out .ssh/known_hosts
ssh to ip defined in pSSID-testpoints

```
ansible-playbook \
  -u ubuntu --ask-pass --become-method sudo \
  -i ansible-inventory-pssid-ilab/inventory \
  ansible-inventory-pssid-ilab/playbooks/bootstrap.yml
```

```
ansible-playbook \
  --user epcjr \
  --ask-pass \
  --ask-become-pass \
  -i ansible-inventory-pssid-ilab/inventory \
  ansible-inventory-pssid-ilab/playbooks/bootstrap.yml
```

Regular provisioning:

Use Ansible ping to verify connectivity to targets:

```
ansible all \
  --ask-become-pass \
  --become-method su \
  -i ansible-inventory-pssid-template/inventory \
  -m ping
```

Run the playbook:

```
ansible-playbook \
  --ask-pass \
  --ask-become-pass \
  -i ansible-inventory-pssid-template/inventory \
  pSSID.yml
```

# Management Commands:

Display auth interfaces on Archivers:

```
ansible ps-archives \
  --ask-pass --ask-become-pass \
  --become-method su \
  -i ansible-inventory-netbasilisk-perfsonar/inventory \
  -a "/usr/sbin/esmond_manage list_user_ip_address"
```

Delete an auth interface on Archivers:

```
ansible ps-archives \
  --ask-pass --ask-become-pass \
  --become-method su \
  -i ansible-inventory-netbasilisk-perfsonar/inventory \
  -a "/usr/sbin/esmond_manage delete_user_ip_address USERNAME IPADDR"
```

**Elastic Development**:

---

Bootstrap

```
git clone https://github.com/UMNET-perfSONAR/ansible-playbook-pSSID.git
cd ansible-playbook-pSSID
cd roles
git clone git@github.com:UMNET-perfSONAR/ansible-role-elastic.git
cd ..
git clone https://github.com/UMNET-perfSONAR/ansible-inventory-pssid-ilab.git
ansible-galaxy install -r requirements.yml --ignore-errors
ansible elastic \
  --ask-pass \
  --ask-become-pass \
  --become-method sudo \
  --inventory ansible-inventory-pssid-ilab/inventory \
  -m ping
```

Provision Elastic

```
ansible-playbook \
  --ask-pass \
  --ask-become-pass \
  --become-method sudo \
  --limit elastic, \
  --inventory ansible-inventory-pssid-ilab/inventory \
  pSSID.yml
```