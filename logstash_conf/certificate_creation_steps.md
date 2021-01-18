CSR ceritificate creation, more secure but requires CA sign. The 'csr' mode generates certificate signing requests that can be sent to
a trusted certificate authority
```
cd /usr/share/elasticsearch/
bin/elasticsearch-certutil csr -name kibana -dns http://141.211.232.46:5601/
unzip kibana-server.zip
```

The 'ca' mode generates a new 'certificate authority'
This will create a new X.509 certificate and private key that can be used
to sign certificate when running in 'cert' mode.
By default the 'ca' mode produces a single PKCS#12 output file which holds:
    * The CA certificate
    * The CA's private key

```
cd /usr/share/elasticsearch/
bin/elasticsearch-certutil ca
```
This will prompt user to enter PKCS#12 output file name and password for this file. Default: elastic-stack-ca.p12


Then use this newly created CA to create certificate. The 'cert' mode generates X.509 certificate and private keys:

```
bin/elasticsearch-certutil cert --ca elastic-stack-ca.p12

```
If the CA was password protected, this command will ask for password and then prompt for a new certificate file name. Default: elastic-certificates.p12


**Certificates for use on http**

```
bin/elasticsearch-certutil http
```
Follow the prompts, use existing CA(elastic-stack-ca.p12)



```
bin/elasticsearch-keystore add xpack.security.http.ssl.keystore.secure_password

```

**Make sure elk can refer to the certificate**

copy over the .pem/.p12 cerficate to elk config files
```
cd /usr/share/elasticsearch
unzip elasticsearch-ssl-http.zip
cp elasticsearc/http.12 /etc/elasticsearch
cp kibana/elasticsearc-ca.pem /etc/kibana
cp kibana/elasticsearc-ca.pem /etc/logstash
```

**Edit files**

Make sure each file has these options enabled. usernames and passwords can be found in `/etc/perfsonar/elastic/auth_setup.out`

```
/etc/logstash/logstash.yml:
xpack.monitoring.enabled: true
xpack.monitoring.elasticsearch.username: <username>
xpack.monitoring.elasticsearch.password: <password>
xpack.monitoring.elasticsearch.hosts: ["https://141.211.232.46:9200"]
xpack.monitoring.elasticsearch.ssl.certificate_authority: "/etc/logstash/elasticsearch-ca.pem"
```

```
/etc/logstash/kibana.yml:
elasticsearch.hosts: ["https://141.211.232.46:9200"]
...
elasticsearch.username: <username>
elasticsearch.password: <password>
...
xpack.security.enabled: true
xpack.watcher.enabled: true
elasticsearch.ssl.certificateAuthorities: ["/etc/kibana/elasticsearch-ca.pem"]
```

```
/etc/elasticsearch/elasticsearch.yml
discovery.seed_hosts: ["127.0.0.1", "[::1]"]
network.host: 0.0.0.0
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate
xpack.security.transport.ssl.keystore.path: /etc/elasticsearch/elastic-cert.p12
xpack.security.transport.ssl.truststore.path: /etc/elasticsearch/elastic-cert.p12
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: "http.p12"
xpack.security.authc:
  anonymous:
    roles: pscheduler_logstash
    authz_exception: true
```

Also logstash pipeline input-output conf files need to account for this security measure
Each files should look like as follows

```
/etc/logstash/conf.d/99-outputs.conf:
output {
    #If has [test][type] create index using that in name.
    # Also creates index template on logstash startup
    if [test][type] {
        elasticsearch {
            hosts => ["https://localhost:9200"]
            hosts => ["localhost"]
            user => "${LOGSTASH_ELASTIC_USER}"
            password => "${LOGSTASH_ELASTIC_PASSWORD}"
            index => "pscheduler_%{[test][type]}-%{+YYYY.MM.dd}"
            template => "/usr/share/logstash/pipeline/index_templates/pscheduler.json"
            template_name => "pscheduler"
            template_overwrite => true
            cacert => '/etc/logstash/elasticsearch-ca.pem'
            ssl => true
            ssl_certificate_verification => false
        }
    }
}
```

```
/etc/logstash/pssid_conf.d/pssid-input-output.conf:
input {
    # Input events are flows from the named rabbit queue on LOCALHOST
    # The following works if the rabbitmq username and password are in the logstash keystore as
    # rabbitmq_input_username and rabbitmq_input_pw. You can also type in the username and pw here, in quotes.
    # Replace the queue and key name, if needed.

    rabbitmq{
        host     => "${rabbitmq_input_host:localhost}"
        user     => "${rabbitmq_input_username:guest}"
        password => "${rabbitmq_input_pw:guest}"
        queue    => 'pSSID'
        #key      => 'pscheduler_raw'
        #exchange => 'amq.direct'
        #durable  => true
        #connection_timeout => 10000
        #subscription_retry_interval_seconds => 5
    }


}
output {
    #If has [test][type] create index using that in name.
    # Also creates index template on logstash startup
    elasticsearch {
        hosts => ["https://localhost:9200"]
        hosts => ["localhost"]
        user => "${LOGSTASH_ELASTIC_USER}"
        password => "${LOGSTASH_ELASTIC_PASSWORD}"
        index => "pssid"
        template => "/usr/share/logstash/pipeline/index_templates/pscheduler.json"
        template_name => "pscheduler"
        template_overwrite => true
        cacert => "/etc/logstash/elasticsearch-ca.pem"
        ssl => true
        ssl_certificate_verification => false
    }
}
```
