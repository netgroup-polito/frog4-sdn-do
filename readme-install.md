# FROG4 OpenDayLight Domain Orchestrator - Installation Guide

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
	git clone https://github.com/netgroup-polito/frog4-odl-do.git
    cd frog4-odl-do
    git submodule init && git submodule update
```

### Write your own configuration

Edit [./default-config.ini](/config/default-config.ini).

Pay attention to all paths: they must be relative paths (respect of 'frog4-odl-do' directory).


### Create the database
```sh
		$ python3 ./scripts/create_database.py
```
Set full permissions on the database file:
```sh
		$ chmod 777 db.sqlite3
```
The only user is "admin" (username:admin, password:admin, tenant:admin_tenant).
All the tables will be empty, except "user" and "tenant".


### Start the Domain Orchestrator
```sh
		$ gunicorn -b 0.0.0.0:9000 -t 500 start:app
```

### Utility scripts

* Reset database and clean all switches.
```sh
		$ python3 ./scripts/clean_all.py
```

* Print the network topology detected by OpenDayLight Domain Orchestrator.
```sh
		$ python3 ./scripts/network_topology.py
```
