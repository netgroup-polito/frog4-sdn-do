# FROG4 SDN Domain Orchestrator - Installation Guide

The following instructions have been tested on Ubuntu 16.04.

## Install the SDN controller 

The SDN domain orchestrator supports both ONOS and OpenDaylight as SDN controllers.

### Install the ONOS SDN controller

ONOS requires JAVA 8 and some other tools:

	$ sudo add-apt-repository ppa:webupd8team/java
	$ sudo apt-get update
	$ sudo apt-get install oracle-java8-installer curl git

It is recommended to build ONOS from source code.

Download the latest version of ONOS from the git repository. Please note that this repository **must** be cloned in your home folder.

	$ git clone https://gerrit.onosproject.org/onos
	$ cd onos
	$ git checkout tags/1.9.0

Build ONOS with buck

	$ tools/build/onos-buck build onos --show-output
	
To be able to execute the ONOS commands, execute the following steps on your home folder:

	$ cd ~
	$ mkdir Downloads Applications
	$ cd Downloads
	$ wget http://archive.apache.org/dist/karaf/3.0.5/apache-karaf-3.0.5.tar.gz
	$ tar -zxvf apache-karaf-3.0.5.tar.gz -C ../Applications/
	$ nano ~/.bashrc
	# At the end of the file, add the following lines 
	#   . ~/onos/tools/dev/bash_profile
	#   export PATH=$PATH:~/Applications/apache-karaf-3.0.5/bin

### Install the OpenDaylight SDN controller [Deprecated]

OpenDayLight requires JAVA 7:

	$ sudo add-apt-repository ppa:webupd8team/java
	$ sudo apt-get update
	$ sudo apt-get install oracle-java7-installer

Download and install OpenDaylight as described in [OpenDaylight - Releases and Guides](https://www.opendaylight.org/downloads).


## Set up the SDN network

The SDN domain orchestrator can operate both on a virtual SDN network and on a physical SDN network.

### Virtual network
If you want to deploy the SDN domain orchestrator on a virtual network managed by ONOS, you can follow the ONOS+Mininet tutorial available at [Environment setup with Mininet and onos.py](https://wiki.onosproject.org/display/test/Environment+setup+with+Mininet+and+onos.py) in order to install Mininet, deploy your topology and start ONOS.

For the sake of completeness, we report here the mandatory steps:

	$ sudo apt-get install bridge-utils
	$ git clone http://github.com/mininet/mininet
	$ mininet/util/install.sh -nvfw
	# Make sure that Mininet works using the following command
	$ sudo mn --test pingall
	
You can create a simple network topology and start ONOS as follows:

	$ cd ~/onos/tools/dev/mininet
	$ sudo mn --custom onos.py --controller onos,1 --topo tree,2,2

After this procedure, ONOS can be reached through its REST API at the URL: `192.168.123.1:8181/onos/ui` .
The username is `onos`, the password is `rocks`.

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
	$ cd [frog4-sdn-do]
	$ python3 -m scripts.create_database
```
Set full permissions on the database file:
```sh
	$ chmod 777 db.sqlite3
```
The script above also adds in the database the `admin` user (`username:admin`, `password:admin`, `tenant:admin_tenant`).

All the tables will be empty, except "user" and "tenant".

#### How to create new user

In order to add a new user you can run the following script (where tenant and e-mail are optional parameters):

        $ python3 -m scripts.add_user userexample usersecretpassword -t usertenant -m userexample@a.com


### SDN domain orchestrator configuration file

Edit [./default-config.ini](/config/default-config.ini) following the instructions that you find inside the file itself and rename it in "config.ini".
The most important field that you have to consider are described in the following.

In the section `[domain_orchestrator]`, set the field `port` to the TCP port to be used to interact with the SDN domain orchestrator through its REST API.

In the [config](/config/) folder, make a new copy of the file `description.json` and rename it (e.g. `OnosResourceDescription.json`). Then, in the [configuration file](/config/default-config.ini) section `[domain_description]`, change the path in the `domain_description_file` field so that it points to the new file (e.g. `domain_description_file = config/OnosResourceDescription.json`).

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
Note that it is enough to install the application; the SDN domain orchestrator will take care of activating it at the system bootstrapping.

* If you are using the SDN domain orchestrator on an ovsdb-based network (e.g., Mininet) and you need to deploy service graphs with GRE-endpoints, or you need to attach phisical ports to your network, you **must instal**l (on ONOS) the [ovsdb-rest bundle](https://github.com/netgroup-polito/onos-applications/tree/master/ovsdb-rest). You can enable/disable support for ovsdb through the `ovsdb_support` flag in the `[ovsdb]` section of the [configuration file](/config/default-config.ini). The configuration file also conains the section `physical_ports`,) where you can specify which interface you want to add to your network, and which is the bridge that should be used to set up GRE tunnels.
Note that it is enough to install the application; the SDN domain orchestrator will take care of activating and configuring it at the system bootstrapping.

Another version of the same bundle is also available in the official [opennetworkinglab repository](https://github.com/opennetworkinglab/onos-app-samples/tree/master/ovsdb-rest).

# Adding the WEB GUI on top of the SDN domain orchestrator

It is possible to configure the [FROG4 GUI](https://github.com/netgroup-polito/fg-gui), so that it can be used to interact with the SDN domain orchestrator (e.g., to deploye new service graphs, or to read the service graphs currently deployed).
To install the GUI, follows the [instructions](https://github.com/netgroup-polito/fg-gui/blob/master/README_INSTALL.md) provided with the repository.

# Start the SDN domain orchestrator

```sh
	$ ./start.sh [-d conf-file]
```

# Utility scripts

The [scripts](https://github.com/netgroup-polito/frog4-sdn-do/tree/master/scripts) folder contains many useful scripts.
Some examples are the following:

* Reset database and clean every switch.
```sh
	$ python3 -m scripts.clean_all
```

* Print the network topology detected by OpenFlow Domain Orchestrator.
```sh
	$ python3 -m scripts.network_topology
```
