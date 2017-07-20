"""
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta
@author: gabrielecastellano

This script starts the web server and has to be called via gunicorn.
Write in the shell:
    $ gunicorn -b 0.0.0.0:9000 -t 500 main:app

Otherwise, make a python script with this two rows:
    from subprocess import call
    call("gunicorn -b 0.0.0.0:9000 -t 500 main:app", shell=True)

Script phases:
   1) Load configuration;
   2) start flask web framework;
   3) add api paths.
"""

import logging
import time
from threading import Thread

from flask import Flask

from do_core.api.api import root_blueprint
from do_core.api.nffg import api as nffg_api
from do_core.api.network_topology import api as topology_api
from do_core.api.user import api as user_api

from do_core.config import Configuration
from do_core.sql.sql_server import try_session
from do_core.domain_information_manager import DomainInformationManager
from do_core.netmanager import NetManager

# Database connection test
try_session()

# initialize logging
Configuration().log_configuration()
print("[ Configuration file is: '" + Configuration().conf_file + "' ]")

logging.debug("SDN Domain Orchestrator Starting...")

# Rest application
if nffg_api is not None and topology_api is not None and user_api is not None:
    app = Flask(__name__)
    app.register_blueprint(root_blueprint)
    logging.info("Flask Successfully started")

# ovsdb
if Configuration().OVSDB_SUPPORT:
    NetManager().init_ovsdb()

# adding physical interfaces if any
if len(Configuration().PORTS) > 0:
    if Configuration().OVSDB_SUPPORT:
        try:
            net_manager = NetManager()
            time.sleep(2)
            ports = Configuration().PORTS
            for port in ports:
                net_manager.add_port(ports[port], port)
        except Exception as ex:
            logging.exception(ex)
            logging.warning('Application ovsdbrest is not available')
    else:
        logging.warning('Physical ports to attach found on the config file, however support for ovsdb is not enabled')

# starting DomainInformationManager
domain_information_manager = DomainInformationManager()
thread = Thread(target=domain_information_manager.start)
thread.start()
logging.info("DoubleDecker client successfully started")

print("Welcome to 'SDN Domain Orchestrator'")
