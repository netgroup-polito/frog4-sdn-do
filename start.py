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
from odl_do.config import Configuration

# SQL Session
from odl_do.sql.sql_server import try_session

# REST Interface
from odl_do.rest_interface import OpenDayLightDO_REST_NFFG_Put
from odl_do.rest_interface import OpenDayLightDO_REST_NFFG_Get_Delete
from odl_do.rest_interface import OpenDayLightDO_REST_NFFG_Status
from odl_do.rest_interface import OpenDayLightDO_UserAuthentication

# Configuration
conf = Configuration()
conf.log_configuration()

# Database connection test
try_session()

# START OPENDAYLIGHT DOMAIN ORCHESTRATOR
logging.debug("OpenDayLight Domain Orchestrator Starting...")
    
# Falcon
logging.info("Starting server application")
app = falcon.API()

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

# [ PUT ]
rest_interface_put = OpenDayLightDO_REST_NFFG_Put()
app.add_route('/NF-FG', rest_interface_put)

# [ DELETE, GET (id) ]
rest_interface_get_delete = OpenDayLightDO_REST_NFFG_Get_Delete()
app.add_route('/NF-FG/{nffg_id}', rest_interface_get_delete)

# [ STATUS (id) ]
rest_nffg_status = OpenDayLightDO_REST_NFFG_Status()
app.add_route('/NF-FG/status/{nffg_id}', rest_nffg_status)

# [ USER AUTH ]
rest_user_auth = OpenDayLightDO_UserAuthentication()
app.add_route('/authentication', rest_user_auth)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

logging.info("Falcon Successfully started")
print("Welcome to 'OpenDayLight Domain Orchestrator'")


    
    
