# Domain Information Library

This library models information about a technological domain used by the frog-orchestrator.
Each domain is described in terms of ***Capabilities*** and ***Hardware***.

Concerning the capabilities, they are divided in:
  * ***Functional Capabilities:*** describe punctual services (e.g., Network Function) that the domain can provide, without giving implementation details about them.
  * ***Infrastructural Capabilities:*** describe technologies that the domain is able to exploit to implement a class of services.

Hardware information includes:
  * ***Interfaces:*** list of boundary interfaces of the domain, each one associated with the information about configuration, neighbors, and technologies that can be used to set up the inter domain traffic steering. 
  * ***Resources:*** computational resources available such as CPU, memory, storage.

This library is Python 2/3 compatible and is referenced as a submodule in all projects that use it.

### Data Model

The domain information schema is a YANG data model, that extends the Openconfig one. You can find it in the [data_model](data_model) folder.
The folder also contains a [tree view](data_model/netgroup-domain_tree.txt) of the data model, other than valid json and xml instances.

### Validation

The [validation readme](README_VALIDATION.md) contains some instructions useful if you need to validate an instance by your own.  
