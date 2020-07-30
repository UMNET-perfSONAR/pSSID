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

If you have your own inventory, clone this inventory in the playbook dir at this point


Get the required roles (ignore errors so we can run this multiple times):

```
ansible-galaxy install -r requirements.yml --ignore-errors
```

Define testpoints, add ip address of the testpoint under [pSSID-testpoints]:

```
vi inventory/hosts
```

Regular provisioning:

Use Ansible ping to verify connectivity to targets:

```
ansible all \
  --ask-become-pass \
  --become-method su \
  -i inventory \
  -m ping
```

Run the playbook:

```
ansible-playbook \
  --ask-pass \
  --ask-become-pass \
  -i inventory \
  pSSID.yml
```


