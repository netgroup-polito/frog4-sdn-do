"""
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta

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
from flasgger import Swagger

# Configuration Parser
from do_core.config import Configuration

# SQL Session
from do_core.sql.sql_server import try_session

# REST Interface
from do_core.rest_interface import DO_REST_NFFG_GPUD
from do_core.rest_interface import DO_REST_NFFG_Status
from do_core.rest_interface import DO_UserAuthentication
from do_core.rest_interface import DO_NetworkTopology

from do_core.domain_information_manager import DomainInformationManager
from do_core.netmanager import NetManager, OvsdbManager

# Database connection test
try_session()

# initialize logging
Configuration().log_configuration()

# START NETWORK CONTROLLER DOMAIN ORCHESTRATOR
logging.debug("Network Controller Domain Orchestrator Starting...")
"""
# Falcon
logging.info("Starting server application")
app = falcon.API()

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

# [ PUT, UPDATE, DELETE, GET (id) ]
rest_interface_gpud = DO_REST_NFFG_GPUD()
app.add_route('/NF-FG/{nffg_id}', rest_interface_gpud)

# [ STATUS (id) ]
rest_nffg_status = DO_REST_NFFG_Status()
app.add_route('/NF-FG/status/{nffg_id}', rest_nffg_status)

# [ USER AUTH ]
rest_user_auth = DO_UserAuthentication()
app.add_route('/login', rest_user_auth)

# [ NETWORK TOPOLOGY ]
rest_net_topology = DO_NetworkTopology()
app.add_route('/topology', rest_net_topology)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
"""
app = Flask(__name__)

swagger_config = {
    "swagger_version": "2.0",
    "title": "FROG4 - OpenFlow Domain Orchestrator API",
    "headers": [
         ('Access-Control-Allow-Origin', '*')
    ],
    "specs": [
        {
            "version": "1.0.0",
            "title": "OpenFlow DO API",
            "endpoint": 'v1_spec',
            "route": '/v1/spec',
        }
    ],
    "static_url_path": "/apidocs",
    "static_folder": "swaggerui",
    "specs_route": "/specs"
}

Swagger(app, config=swagger_config)

orch = DO_REST_NFFG_GPUD.as_view('NF-FG')
app.add_url_rule(
    '/NF-FG/<nffg_id>',
    view_func=orch,
    methods=["GET", "PUT", "DELETE"]
)

nffg_status = DO_REST_NFFG_Status.as_view('NFFGStatus')
app.add_url_rule(
    '/NF-FG/status/<nffg_id>',
    view_func=nffg_status,
    methods=["GET"]
)

login = DO_UserAuthentication.as_view('login')
app.add_url_rule(
    '/login',
    view_func=login,
    methods=["HEAD", "POST"]
)
network_topology = DO_NetworkTopology.as_view('network_topology')
app.add_url_rule(
    '/topology',
    view_func=network_topology,
    methods=["GET"]
)
logging.info("Flask Successfully started")
print("Welcome to 'Network Controller Domain Orchestrator'")


# adding physical interfaces if any
try:
    OvsdbManager().activate_ovsdbrest()
    OvsdbManager().configure_ovsdbrest()
    time.sleep(2)
    # physical interfaces
    ports = Configuration().PORTS
    for port in ports:
        OvsdbManager().add_port(ports[port], port)
except Exception as ex:
    logging.exception(ex)
    logging.warning('Application ovsdbrest is not available')

# starting DomainInformationManager
domain_information_manager = DomainInformationManager()
thread = Thread(target=domain_information_manager.start)
thread.start()
