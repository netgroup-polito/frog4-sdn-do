# FROG4 OpenFlow Domain Orchestrator

This orchestrator supervises an OpenFlow domain - constituited only by several switches - 
and provides traffic steering capabilities between its endpoints.


## Traffic Steering

This domain expects to receive endpoint-to-endpoint flowules only, and these flowrules
must be compliant with OpenFlow1.0.

Every flowrule must have one entry endpoint and only one output endpoint (multiple output not supported!);
a flowrule is instantiated into every switch belonging the path between the two endpoints.

Every flow is distinguished by a vlan id, in order to avoid ambiguities, duplicities, and other 
similar troubles into the involved switches.


## The "Big Switch"

This domain hides the internal details (switches and the links between them),
so it advertises itself as a 'big switch' with several well-defined endpoints.

In particular, as you can see in [./config/ResourceDescription.example.json](/config/ResourceDescription.example.json),
for each endpoint we can specify:
* if it is enabled to be used as "entry endpoint";
* all the entry vlan ids, used to match the incoming packets.

A domain administrator has to add and configure the endpoints editing the file
[./config/ResourceDescription.json](/config/ResourceDescription.json).


## DoubleDecker and ResourceDescription.json

To advertise the features and the capabilities of this domain, we use
[DoubleDecker messaging systems](https://github.com/Acreo/DoubleDecker).

In particular, the file [./config/ResourceDescription.json](/config/ResourceDescription.json) is published
under the topic "NF-FG", both at the start of the domain orchestrator and after any database change.

Note: set the appropriate broker address in [./config/default-config.ini](/config/default-config.ini).


## NF-FG Library

All the graphs sended via REST API must respect the NF-FG json schema.

Pay specifical attention to the information that are not supported by this domain orchestrator:
* VNFs;
* Remote endpoints;
* "TTL" field of the endpoints;
* Endpoints that are meither "interface" type nor "vlan" type;
* Flowrule actions with multiple outputs, "output_to_controller" or "output_to_queue".

Note: the nf-fg library is a sub-module of this repository.


## REST APIs

A global orchestrator should communicate through the REST APIs provided by this domain orchestrator.

REST interface provides several urls to authenticate, to send/get/delete a graph, to get the status of a graph.

#### Basic authentication
This step is needed to retrieve a token which will be used into all the operative requests. 
```
	[POST]
	Url: '/login'
	Content-Type: application/json
	Data: { "username":"admin", "password":"admin" }
```
Response is the token:
```
	797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```

#### Token authentication
Check if the token is still valid.
```
	[POST]
	Url: '/login'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```


#### Send a new graph or update an existent graph
```
	[PUT]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
	Content-Type: application/json
	Data: { "forwarding-graph": { "id": "12345", "name": "GraphName", ... } }
```

#### Get a graph
```
	[GET]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```
Response:
```
	{
		"forwarding-graph":
		{
			"id": "12345", 
			"name": "GraphName", 
			...
		}
	}
```

#### Delete a graph
```
	[DELETE]
	Url: '/NF-FG/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```

#### Get the status of a graph
```
	[GET]
	Url: '/NF-FG/status/12345'
	X-Auth-Token: 797187d548d937827b53a7e6f3d3ff7fb1ead5d9887480fd71eb97971535bf1d
```
Response is the status:
```
	completed
```


  
