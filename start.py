'''
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta

This script starts the web server and has to be called via gunicorn.
Write in the shell:
    $ gunicorn -b 0.0.0.0:9000 -t 500 start:app

Otherwise, make a python script with this two rows:
    from subprocess import call
    call("gunicorn -b 0.0.0.0:9000 -t 500 start:app", shell=True)

Script phases:
   1) Load configuration;
   2) start falcon web framework;
   3) add api paths.
'''

import logging, falcon

# Configuration Parser
from do_core.config import Configuration

# SQL Session
from do_core.sql.sql_server import try_session

# REST Interface
from do_core.rest_interface import OpenDayLightDO_REST_NFFG_GPUD
from do_core.rest_interface import OpenDayLightDO_REST_NFFG_Status
from do_core.rest_interface import OpenDayLightDO_UserAuthentication
from do_core.rest_interface import OpenDayLightDO_NetworkTopology

from do_core.messaging import Messaging

# Database connection test
try_session()

# START OPENDAYLIGHT DOMAIN ORCHESTRATOR
logging.debug("OpenDayLight Domain Orchestrator Starting...")
    
# Falcon
logging.info("Starting server application")
app = falcon.API()

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

# [ PUT, UPDATE, DELETE, GET (id) ]
rest_interface_gpud = OpenDayLightDO_REST_NFFG_GPUD()
app.add_route('/NF-FG/{nffg_id}', rest_interface_gpud)

# [ STATUS (id) ]
rest_nffg_status = OpenDayLightDO_REST_NFFG_Status()
app.add_route('/NF-FG/status/{nffg_id}', rest_nffg_status)

# [ USER AUTH ]
rest_user_auth = OpenDayLightDO_UserAuthentication()
app.add_route('/login', rest_user_auth)

# [ NETWORK TOPOLOGY ]
rest_net_topology = OpenDayLightDO_NetworkTopology()
app.add_route('/topology', rest_net_topology)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

logging.info("Falcon Successfully started")
print("Welcome to 'OpenDayLight Domain Orchestrator'")

Messaging().PublishDomainConfig()


    
    
