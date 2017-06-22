# FROG4 SDN Domain Orchestrator

This orchestrator supervises an SDN based domain (e.g., OpenFlow devices managed by an ONOS Controller) - constituited only by several switches - and provides traffic steering capabilities between its endpoints.
It always affors the possibility to insert simple NFs (such as a NAT) on the flow path (the proper bundle shuld be installed on the SDN Controller)


## Traffic Steering

This domain expects to receive endpoint-to-endpoint flowules must be compliant with OpenFlow1.0.

Every flowrule must have one entry endpoint and only one output endpoint (multiple output are not supported!);
a flowrule is instantiated into every switch belonging the path between the two endpoints.

Every flow is internally distinguished by a vlan id, in order to avoid ambiguities, duplicities, and other 
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
The final json should be compliant against this [YANG data model](https://github.com/netgroup-polito/domain-information-library).

## Network Functions

The SDN domain orchestrator also provide the possibility to deploy some NFs (implemented with an SDN application) between endpoints. The SDN application must allow a fine configuration in order to properly set physical interface with which interact. A supported application is this [ONOS NAT bundle](https://github.com/netgroup-polito/onos-applications/tree/master/nat)

Currently just chains (endpoint to endpoint paths) with up to one NF are supported.

## SDN Controllers

This project leans on a SDN controller to have some network informations and
for each openflow-based operation (e.g. create and delete flow rules).

Currently, the DO supports [ONOS](http://onosproject.org/) (>= 1.5.0 "Falcon")

Support for [OpenDayLight](https://www.opendaylight.org/) has been deprecated.


## DoubleDecker and ResourceDescription.json

To advertise the features and the capabilities of this domain, we use
[DoubleDecker messaging systems](https://github.com/Acreo/DoubleDecker).

In particular, the file [./config/ResourceDescription.json](/config/ResourceDescription.json) is published
under the topic "NF-FG", both at the start of the domain orchestrator and after any database change.

Note: set the appropriate broker address in [./config/default-config.ini](/config/default-config.ini).


## NF-FG Library

All the graphs sended via REST API must respect the NF-FG json schema.

Pay specifical attention to the information that are not supported by this domain orchestrator:
* NF to NF links;
* Remote endpoints;
* "TTL" field of the endpoints;
* Flowrule actions with multiple outputs, "output_to_controller" or "output_to_queue".

Note: the nf-fg library is a sub-module of this repository.

## REST APIs

A global orchestrator should communicate through the REST APIs provided by this domain orchestrator.

REST interface provides several urls to authenticate, to send/get/delete a graph, to get the status of a graph.

In order to discover which REST calls are supported you can see the API documentation at the URL {do-address:do-port}/api_docs once the domain orchestrator is installed and running (e.g., `127.0.0.1:10000/api_docs`).

## Use cases

Use cases examples are in the [use_cases](./use_cases) folder.
There, for each use case you can find condifiguration scripts, NF-FG and more.

