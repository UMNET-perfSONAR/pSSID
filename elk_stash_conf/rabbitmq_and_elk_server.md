# Setting up Rabbitmq

The playbook [ansible-playbook-pSSID](https://github.com/UMNET-perfSONAR/ansible-playbook-pSSID) includess roles that installs rabbitmq on the probes. The playbook uses [ansible-role-rabbitmq](https://github.com/UMNET-perfSONAR/ansible-role-rabbitmq). 

For the elk server, [ansible-playbook-elastic](https://github.com/UMNET-perfSONAR/ansible-playbook-elastic) includes roles that installs rabbitmq. Following the instructions for this play book sets up elk and rabbitmq.

---

**pSSID and Rabbitmq**

Currently, pSSID uses python pika library to create and send messages to rmq queue. The scan and coverage results are sent to remote elk server rmq queue using the amqp url. The amqp url is hardcoded in the source code and needs to be changed if machine changes. The use of amqp url to send data eliminates the need for elk to know ip addresses of each probe. TODO: change the hardcoded url. 


---

Commands to make sure rmq on elk receives messages:
	
for each probe:
```
firewall-cmd --permanent --zone=public --add-port=5672/tcp
```

Elk Server:
```
systemctl status firewalld
systemctl stop firewalld
```
