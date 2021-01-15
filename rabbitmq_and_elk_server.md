# Run the commands to set up logstash pipeline
Old method:	
	
Pi:

```
rabbitmqctl list_users
rabbitmqctl add_user [USERNAME] [PASSWORD]
rabbitmqctl set_permissions -p / [USERNAME] “.*” “.*” “.*”
systemctl status rabbitmq-server	     
systemctl status firewalld
systemctl stop firewalld
```



Elk Server:
```
cd /etc/logstash/pssid_conf.d/
# add this object to pssid-input-output.conf for every new pi:
    rabbitmq{
        host     => [Pi's ip addr]
        user     => [USERNAME]
        password => [PASSWORD]
        queue    => "pSSID"
        ...
        optional certificate info
        ...
    }
systemctl restart logstash
/var/log/messages will show if it started successfully
```


New method:
	
Pi:
```
firewall-cmd --permanent --zone=public --add-port=5672/tcp
```

Elk Server:
```
systemctl status firewalld
systemctl stop firewalld
```
