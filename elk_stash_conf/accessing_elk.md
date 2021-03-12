# Accessing ELK


---

**Through command line**


1. Connect to UM-VPN
2. ssh to bastion
3. ssh to pssid-elk.miserver.it.umich.edu or using ip 141.211.232.46
4. run a curl command: `curl -k -X GET https://localhost:9200`

This curl command returns a snapshot elasticsearch configuration such as name, version etc. If the command is successful and elasticsearch is running it should return:

```
{
  "name" : "pssid-elk.miserver.it.umich.edu",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "[redacted]",
  "version" : {
    "number" : "7.11.1",
    "build_flavor" : "default",
    "build_type" : "rpm",
    "build_hash" : "[redacted]",
    "build_date" : "2021-02-15T13:44:09.394032Z",
    "build_snapshot" : false,
    "lucene_version" : "8.7.0",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}

```


Elasticsearch has various APIs that can be use to create or update users, access role, edit security poliices.

To create a user:

```
curl -k -u elastic \
-X POST https://localhost:9200/_security/user/jacknich?pretty" \
-H 'Content-Type: application/json' -d \
'
{
  "password" : "l0ng-r4nd0m-p@ssw0rd",
  "roles" : [ "admin", "other_role1" ],
  "full_name" : "Jack Nicholson",
  "email" : "jacknich@example.com"
}
'
```

This will create user with username jacknich. If successful, it will return 
```
{
	"created": true
}
```

---

**Through Browser**

1. Connect to UM-VPN
2. go to http://141.211.232.46:5601/

If elasticsearch and kibana are running, the website will prompt for username and password. A user can be created through bastion using the method above. 

After logging in, user can access the kibana dashboards and data.