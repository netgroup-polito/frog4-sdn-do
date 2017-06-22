# FROG4 OpenFlow Domain Orchestrator - Installation Guide

## Set up the SDN network

The SDN domain orchestrator can operate both on a virtual SDN network and on a physical SDN network.

### Virtual network
If you want to deploy the SDN domain orchestrator on a virtual network managed by ONOS, please follow the ONOS+Mininet tutorial available at [Environment setup with Mininet and onos.py](https://wiki.onosproject.org/display/test/Environment+setup+with+Mininet+and+onos.py).

### Physical network

In this case, we assume that your switches are already deployed. Then, you just have to install the OpenFlow controller (either ONOS or OpenDaylight) as follows.

#### Install the ONOS SDN controller

ONOS requires JAVA 8:

	$ sudo add-apt-repository ppa:webupd8team/java
	$ sudo apt-get update
	$ sudo apt-get install oracle-java8-installer

It is recommended to build ONOS from source code.

Download the latest version of ONOS from the git repository:

	$ git clone https://gerrit.onosproject.org/onos

Build ONOS with buck

	$ cd ONOS
	$ tools/build/onos-buck build onos --show-output

###### Use Cases

Follow the instructions provided in [](use_cases/) for particular setup needed by the use-case you need to reproduce (e.g., nat-sdn-demo).

#### Install the OpenDaylight SDN controller

OpenDayLight requires JAVA 7:

	$ sudo add-apt-repository ppa:webupd8team/java
	$ sudo apt-get update
	$ sudo apt-get install oracle-java7-installer

Download and install OpenDaylight as described in [OpenDaylight - Releases and Guides](https://www.opendaylight.org/downloads).

## Install the SDN domain orchestrator

### Install dependecies

	$ sudo apt-get install curl sqlite3 python3-pip
	$ sudo pip3 install flask==0.12 flask-restplus==0.9.2 gunicorn==19.6.0 networkx==1.10 requests==2.9.1 configparser==3.5.0 jsonschema==2.6.0 sqlalchemy==1.1.6

To check if a module is already installed and its version:

	$ pip3 freeze
	
#### Install the DoubleDecker client
The SDN domain orchestrator uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker-py) messaging system to communicate with the FROG4-orchestrators. Then, you need to install the DoubleDecker client.

		$ git clone https://github.com/Acreo/DoubleDecker-py.git		
		$ cd DoubleDecker-py
		$ git reset --hard dc556c7eb30e4c90a66e2e00a70dfb8833b2a652
		$ cp -r [frog4-orchestrator]/patches .
		$ git am patches/doubledecker_client_python/0001-version-protocol-rollbacked-to-v3.patch
		
Now you can install the DubleDeker as follows:

		#install dependencies 
		$ sudo apt-get update
		$ sudo apt-get install python3-setuptools python3-nacl python3-zmq python3-urwid python3-tornado
		# install the doubledecker module and scripts
		$ sudo python3 setup.py install

### Clone the code of the sdn-do

	$ git clone https://github.com/netgroup-polito/frog4-sdn-do
	$ cd frog4-sdn-do
	$ git submodule init && git submodule update

### Write your own configuration

Edit [./default-config.ini](/config/default-config.ini) basing on instructions that you find inside the file itself and rename it in "config.ini".

Pay attention to all paths: they must be relative paths (respect of 'frog4-openflow-do' directory).

In the config folder, make a new copy of the file OnosResourceDescription_static.json and rename it (e.g. OnosResourceDescription.json).
Edit the "config.ini" file in the section "[domain_description]" and change the path in the domain description file to this new file (e.g. domain_description_file = config/OnosResourceDescription.json).


### Set the SDN Controller

The section "[network_controller]" defines the name of the SDN Controller.

According to the SDN Controller name, edit the section [opendaylight] or [onos] 
to specify version, endpoint and credentials.


### Create the database
```sh
	$ python3 -m scripts.create_database
```
Set full permissions on the database file:
```sh
	$ chmod 777 db.sqlite3
```
The only user is "admin" (username:admin, password:admin, tenant:admin_tenant).

All the tables will be empty, except "user" and "tenant".

## Set up the SDN Controller

The SDN controller should be completed with additional bundles that provides needed API to the sdn-do:

1) If you need the support to export available SDN application as NF, you need to install a nf-monitor bundle and activate it. On ONOS, you can use [this bundle](https://github.com/netgroup-polito/onos-applications/tree/master/apps-capabilities), following the instructions provided on the repository. You can enable/disable support for dynamic discovering of capabilities through the discover_capabilities flag in the [configuration file](/config/default-config.ini).

2) If you are using the sdn-do on an ovsdb-based network (e.g., Mininet) and you need to deploy graphs having GRE-endpoints or to attach phisical ports to your network, you need to install (on ONOS) the [ovsdb-rest bundle](https://github.com/opennetworkinglab/onos-app-samples/tree/master/ovsdb-rest). You can enable/disable support for ovsdb through the ovsdb_support flag in the [configuration file](/config/default-config.ini). The configuration file also conains a section (physical_ports) where you can specify which interface you want to add to your network, and which is the bridge that should be used to set up GRE tunnels.


# Start the Domain Orchestrator (HTTP)
```sh
	$ ./start.sh -d config/your_config.ini
```
# Start the Domain Orchestrator (HTTPS)

In this case a certificate is needed.

A useful guide: [Ubuntu: certificates and security](https://help.ubuntu.com/12.04/serverguide/certificates-and-security.html).

Otherwise, you can generate a self-signed certificate executing this script (based on the previous link):
```sh
	$ cd ./keys/certificate
	$ ./certificate.sh
	$ cd ../..
```

Now you can run gunicorn on https:
```sh
	$ gunicorn -b 0.0.0.0:9000 -t 500 \
	--certfile=keys/certificate/server.crt \
	--keyfile=keys/certificate/server.key \
	main:app
```

# Utility scripts

* Reset database and clean every switch.
```sh
	$ python3 -m scripts.clean_all
```

* Print the network topology detected by OpenFlow Domain Orchestrator.
```sh
	$ python3 -m scripts.network_topology
```
