# FROG4 OpenFlow Domain Orchestrator - Installation Guide

## Install the SDN controller 

The SDN domain orchestrator supports both ONOS and OpenDaylight as SDN controllers.

### Install the ONOS SDN controller

ONOS requires JAVA 8 and some other tools:

	$ sudo add-apt-repository ppa:webupd8team/java
	$ sudo apt-get update
	$ sudo apt-get install oracle-java8-installer curl git

It is recommended to build ONOS from source code.

Download the latest version of ONOS from the git repository:

	$ git clone https://gerrit.onosproject.org/onos

Build ONOS with buck

	$ cd ONOS
	$ tools/build/onos-buck build onos --show-output

#### Use Cases

Follow the instructions provided in [](use_cases/) for particular setup needed by the use-case you need to reproduce (e.g., nat-sdn-demo).

### Install the OpenDaylight SDN controller

OpenDayLight requires JAVA 7:

	$ sudo add-apt-repository ppa:webupd8team/java
	$ sudo apt-get update
	$ sudo apt-get install oracle-java7-installer

Download and install OpenDaylight as described in [OpenDaylight - Releases and Guides](https://www.opendaylight.org/downloads).


## Set up the SDN network

The SDN domain orchestrator can operate both on a virtual SDN network and on a physical SDN network.

### Virtual network
If you want to deploy the SDN domain orchestrator on a virtual network managed by ONOS, please follow the ONOS+Mininet tutorial available at [Environment setup with Mininet and onos.py](https://wiki.onosproject.org/display/test/Environment+setup+with+Mininet+and+onos.py).

After following the procedure, ONOS can be reached through its REST API at the URL: `192.168.123.1:8181`.

### Physical network

In this case, we assume that your switches are already deployed, and you know how to connect them to the SDN orchestrator.

## Install the SDN domain orchestrator

### Install dependecies

	$ sudo apt-get install curl sqlite3 python3-pip git
	$ sudo pip3 install flask==0.12 flask-restplus==0.9.2 gunicorn==19.6.0 networkx==1.10 requests==2.9.1 configparser==3.5.0 jsonschema==2.6.0 sqlalchemy==1.1.6

To check if a module is already installed and its version:

	$ pip3 freeze
	
### Clone the code of the sdn-do

	$ git clone https://github.com/netgroup-polito/frog4-sdn-do
	$ cd frog4-sdn-do
	$ git submodule init && git submodule update
	
### Install the DoubleDecker client
The SDN domain orchestrator uses the [DoubleDecker](https://github.com/Acreo/DoubleDecker-py) messaging system to communicate with the FROG4-orchestrators. Then, you need to install the DoubleDecker client.

		$ git clone https://github.com/Acreo/DoubleDecker-py.git		
		$ cd DoubleDecker-py
		$ git reset --hard dc556c7eb30e4c90a66e2e00a70dfb8833b2a652
		$ cp -r [frog4-sdn-do]/patches .
		$ git am patches/doubledecker_client_python/0001-version-protocol-rollbacked-to-v3.patch
		
Now you can install the DubleDeker as follows:

		#install dependencies 
		$ sudo apt-get update
		$ sudo apt-get install python3-setuptools python3-nacl python3-zmq python3-urwid python3-tornado
		# install the doubledecker module and scripts
		$ sudo python3 setup.py install
		
### Create the SQL database
```sh
	$ python3 -m scripts.create_database
```
Set full permissions on the database file:
```sh
	$ chmod 777 db.sqlite3
```
The only user is `admin` (username:admin, password:admin, tenant:admin_tenant).

All the tables will be empty, except "user" and "tenant".

#### How to create new user

**TODO**

### SDN domain orchestrator configuration file

Edit [./default-config.ini](/config/default-config.ini) following the instructions that you find inside the file itself and rename it in "config.ini".
The most important field that you have to consider are described in the following.

In the section `[domain_orchestrator]`, set the field `port` to the TCP port to be used to interact with the SDN domain orchestrator through its REST API.

In the [config](/config/) folder, make a new copy of the file `description.json` and rename it (e.g. `OnosResourceDescription.json`). Then, in the [confgiuration file](/config/default-config.ini) section `[domain_description]`, change the path in the `domain_description_file` field so that it points to the new file (e.g. `domain_description_file = config/OnosResourceDescription.json`).

In the section `[network_controller]` edit the field `controller_name`, by writing `OpenDayLight` or `ONOS`, according to the SDN controller that you have deployed above.
Then, edit the section `[opendaylight]` or `[onos]` with the proper information.

In the section `[messaging]`, you have to configure the connection towards the broker (note that this guide supposes that, if you need a broker, you have already installed it). Particularly, you can enable/disable the connection towards the broker through the field `dd_activate`, set the URL to be used to contact such a module (`dd_broker_address`) and the file containing the key to be used (`dd_tenant_key`).

Finally, pay attention to all paths, which must be relative paths with respect to the `frog4-openflow-do` directory.

#### JOLNET considerations

If you are going to execute the SDN domain orchestrator on the JOLNET, set to `true` the parameter `jolnet` in the section `[other_options]`. 
Moreover, you have to edit the `available_ids` list in the `vlan` section, by specifying the VLAN ids that are allowd for the traffic steering within the SDN domain.

## Set up the SDN Controller

The SDN controller should be completed with additional bundles that provides needed API to the SDN domain orchestrator:

* If you need to export available SDN application as NF, you **must install** a specific bundle in the SDN controller and activate it. On ONOS, you can use [this bundle](https://github.com/netgroup-polito/onos-applications/tree/master/apps-capabilities), following the instructions provided on the repository. You can enable/disable support for dynamic discovering of capabilities through the `discover_capabilities` flag in the [configuration file](/config/default-config.ini).

* If you are using the SDN domain orchestrator on an ovsdb-based network (e.g., Mininet) and you need to deploy service graphs with GRE-endpoints, or you need to attach phisical ports to your network, you **must instal**l (on ONOS) the [ovsdb-rest bundle](https://github.com/opennetworkinglab/onos-app-samples/tree/master/ovsdb-rest). You can enable/disable support for ovsdb through the `ovsdb_support` flag in the `[ovsdb]` section of the [configuration file](/config/default-config.ini). The configuration file also conains the section `physical_ports`,) where you can specify which interface you want to add to your network, and which is the bridge that should be used to set up GRE tunnels.

# Start the SDN domain orchestrator

The SDN domain orchestrator can be contacted either through HTTP or through HTTP, as described in the following.

## Start the SDN domain orchestrator with HTTP
```sh
	$ ./start.sh [-d conf-file]
```
## Start the SDN domain orchestrator with HTTPS

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
