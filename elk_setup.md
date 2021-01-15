# Installing and Securing ELK

[elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/elasticsearch-intro.html)
Follow the ansible instruction from [ansible-playbook-elastic](https://github.com/UMNET-perfSONAR/ansible-playbook-elastic)


**Elastic Directories**

All the following directories should have owner elasticsearch and be in group elasticsearch(ls -la), otherwise change ownership:
```
sudo chown -R elasticsearch:elasticsearch <directory>
```

This is the default elastic home (ES_HOME) directory where the elastic binaries and dependencies reside:

```
/usr/share/elasticsearch/
```
In ES_HOME directory, elasticsearch can be manually started:
```
./bin/elasticsearch [options]		# check elasticsearch docs for options
```

This is the default elastic config (ES_CONF) directory where elastic.yml and other config files reside:

```
/etc/elasticsearch/
```

Elasticsearch specific errors are logged in:

```
/var/log/elasticsearch/
```

Elasticsearch node config director:
```
/var/lib/elasticsearch
```

Other elasticsearch file locations:
```
/etc/sysconfig/elasticsearch
```


**Logstash Directories**

All the following directories should have owner logstash and be in group logstash(ls -la), otherwise change ownership:
```
sudo chown -R logstash:logstash <directory>
```

This is the default logstash home directory where the logstash binaries and dependencies reside:

```
/usr/share/logstash/
```

This is the default logstash config directory where logstash.yml and other config files reside:

```
/etc/logstash/
```

logstash specific errors are logged in:

```
/var/log/logstash/
```

logstash JAVA_HOME and elasticsearch login user/password should be defined in:
```
/etc/sysconfig/logstash
```


**kibana Directories**

All the following directories should have owner kibana and be in group kibana(ls -la), otherwise change ownership:
```
sudo chown -R kibana:kibana <directory>
```

This is the default logstash home directory where the logstash binaries and dependencies reside:

```
/usr/share/kibana/
```

This is the default kibana config directory where kibana.yml and other config files reside:

```
/etc/kibana/
```

kibana specific errors are logged in:

```
/var/log/kibana/
```


**Built-in Users**

Ansible installation should have created built in users with their passwords in the directory /etc/perfsonar/elastic/
	auth_setup.out contains all the elasticsearch built in users
	elastic_login contains elastic user and password that local curl commands use
	pscheduler_logstash contains user password for pscheduler that will be used when setting up piplines from logstash to elastic


---


After installing with ansible, use the following commands to check the status:

```
systemctl status elasticsearch
systemctl status kibana
systemctl status logstash
```

If there are errrors, check 
```
vi /var/log/messages
```
or
```
journalctl -xe
```
to see systemd errors. Restart each of the service above if necessary.

---


Note: Ansible installation sets most of the configuration in those directories mentioned above. If any errors persist, re-run the commands by hand (not all commands need to be re-run). 

Common error: Ansible 'run secure script' may have failed. Run the following commands:
```
cd /usr/lib/perfsonar/scripts/
./pselastic_secure.sh
```

if there is error similar to 'could not verify user elastic. The password for may have already been changed', then run:
```
cd /usr/share/elasticsearch
bin/elasticsearch-keystore list
```

if bin/elasticsearch list does not output 'bootstrap.password', then add:
```
bin/elasticsearch-keystore add "bootstrap.password"
```
Add a bootstrap password which elasticsearch could use to set up built-in users for elastic, kibana, logstash, etc. Save the password.

Run the secure script again:
```
cd /usr/lib/perfsonar/scripts/
./pselastic_secure.sh
```

Kibana error: it is possible that pselastic_secure.sh changed kibana's password for elasticsearch login. Check kibana.yml and search for 'elasticsearch.username'. Make sure the user adn password correspon with kibana user and password in the built-in users file (/etc/perfsonar/elastic/auth_setup.out)

Logstash Error: Make sure correct JAVA_HOME is defined in /etc/sysconfig/logstash

elasticsearch error: if stops running after patching:
```
cat /proc/mounts | grep /tmp
```
if /tmp is mounted with 'noexec', run:
```
mount -o remount,exec /tmp
```
then restart necessary services

Other errors: make sure the permissions are set appropriately, /tmp is mounted with 'noexec' absent



---


