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


## SDN Controllers

This project leans on a SDN controller to have some network informations and
for each openflow-based operation (e.g. create and delete flow rules).

Currently, the DO supports [OpenDayLight](https://www.opendaylight.org/) and [ONOS](http://onosproject.org/), in particular:
* ONOS 1.5.0 "Falcon"
* OpenDayLight Hydrogen Virtualization 1.0
* OpenDayLight Helium SR4
* OpenDayLight Lithium SR3


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

In order to discover which REST calls are supported you can see the API documentation at the URL {Domain_Orchestrator_Address}/api_docs once the domain orchestrator is installed and running.
