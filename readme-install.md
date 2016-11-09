# FROG4 OpenFlow Domain Orchestrator - Installation Guide

### Install the SDN Controller

[ONOS - Build from source code (recommended)](https://wiki.onosproject.org/display/ONOS/Getting+ONOS#GettingONOS-ONOSSourceCode) or 
[ONOS - Packages and tutorials](https://wiki.onosproject.org/display/ONOS/Download+packages+and+tutorial+VMs)

[OpenDayLight - Releases and Guides](https://www.opendaylight.org/downloads)

ONOS requires JAVA 8:
```sh
	sudo add-apt-repository ppa:webupd8team/java
	sudo apt-get update
	sudo apt-get install oracle-java8-installer
```

OpenDayLight requires JAVA 7:
```sh
	sudo add-apt-repository ppa:webupd8team/java
	sudo apt-get update
	sudo apt-get install oracle-java7-installer
```

Note: both versions can coexist, but you must choose what version to enable:
```sh
	sudo update-alternatives --config java
```


### Install Python 3

```sh
	$ sudo apt-get install python3.4-dev python3-setuptools
	$ sudo easy_install3 pip
```

### Install Python libraries

* [doubledecker](https://github.com/Acreo/DoubleDecker)
* gunicorn 19.4.1
* falcon 0.3.0
* requests 2.9.1
* configparser 3.5.0
* jsonschema 2.5.1
* sqlite3 2.6.0
* sqlalchemy 1.0.11
* networkx 1.10
* flask 0.11.1
* flasgger 0.5.12

To install a python3 module:
```sh
	$ sudo pip3 install <module>
```

To check if a module is already installed and its version:
```sh
	$ pip3 freeze
```

### Clone the code

```sh
	git clone https://github.com/netgroup-polito/frog4-openflow-do.git
	cd frog4-openflow-do
	git submodule init && git submodule update
```

### Write your own configuration

Edit [./default-config.ini](/config/default-config.ini) and rename it in "config.ini".

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


### Start the Domain Orchestrator (HTTP)
```sh
	$ gunicorn -b 0.0.0.0:9000 -t 500 main:app
```

### Start the Domain Orchestrator (HTTPS)

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

### Utility scripts

* Reset database and clean every switch.
```sh
	$ python3 ./scripts/clean_all.py
```

* Print the network topology detected by OpenFlow Domain Orchestrator.
```sh
	$ python3 ./scripts/network_topology.py
```
