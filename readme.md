# FROG4 OpenDayLight Domain Orchestrator

This orchestrator supervises an OpenDayLight domain - constituited only by several switches - 
and provides traffic steering capabilities between his endpoints.


### Traffic Steering

This domain expects to receive endpoint-to-endpoint flowules only, and these flowrules
must be compliant with OpenFlow1.0.

Every flowrule must have one ingress endpoint and only one egress endpoint (multiple output not supported!);
a flowrule is instantiated into every switch belonging the path between the two endpoints.

Every flow will be distinguished by a vlan id, in order to avoid ambiguities, duplicities, and other 
similar troubles into the involved switches.


### The "Big Switch"

This domain hides the internal details (switches and the links between them),
so it advertises itself as a 'big switch' with several well-defined endpoints.

In particular, as you can see in [./config/ResourceDescription.example.json](/config/ResourceDescription.example.json),
for each endpoint we can specify:
* if it is enabled in order to can be used as "ingress endpoint";
* all the ingress vlan ids, used to match the incoming packets.

A domain administrator has to add and configure the endpoints editing the file
[./config/ResourceDescription.json](/config/ResourceDescription.json).


### DoubleDecker and ResourceDescription.json

To advertise the features and the capabilities of this domain, we take advantage of [DoubleDecker messaging systems](https://github.com/Acreo/DoubleDecker).

In particular, the file [./config/ResourceDescription.json](/config/ResourceDescription.json) is published
under the topic "NF-FG", both at the start and when a database change occurs.

N.B. set the appropriate broker address in [./config/default-config.ini](/config/default-config.ini).


### REST API

A global orchestrator should communicate by the REST API provided by this domain orchestrator.

REST interface provides several urls for the authentication, to send/get/delete a NFFG, to get the status of a graph.

##### Basic authentication
This step is needed to retrieve a token which will be used into all the operative requests. 
```
	[POST]
	Url: '/login'
	Content-Type: application/json
	Data: { "username":"admin", "password":"admin" }
```
Response:
```
	{ 
		"token": "797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d"
		"user_id": "1"
	}
```

##### Token authentication
Check if the token is still valid.
```
	[POST]
	Url: '/login'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```
Response:
```
	{ 
		"token": "797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d"
		"user_id": "1"
	}
```


##### Send a new graph or update an existent graph.
```
	[PUT]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
	Content-Type: application/json
	Data: { "forwarding-graph": { "id": "12345", "name": "GraphName", ... }
```

##### Get a graph
```
	[GET]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```


##### Delete a graph
```
	[DELETE]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```

##### Get the status of a graph
```
	[GET]
	Url: '/NF-FG/status/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```



  