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

## Utility scripts

* Reset database and clean all switches.
```sh
		$ python3 ./scripts/clean_all.py
```

* Print the network topology detected by OpenDayLight Domain Orchestrator.
```sh
		$ python3 ./scripts/network_topology.py
```
