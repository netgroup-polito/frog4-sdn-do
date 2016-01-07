'''
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta

This script test has to be called via gunicorn.
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
from odl_ca_core.config import Configuration

# SQL Session
from odl_ca_core.sql.sql_server import try_session

# REST Interface
from odl_ca_core.rest_interface import OpenDayLightCA_REST_NFFG, OpenDayLightCA_REST_NFFGStatus, OpenDayLightCA_UserAuthentication

# Configuration
conf = Configuration()
#conf.log_configuration()

# Database connection test
try_session()

# START OPENDAYLIGHT CONTROL ADAPTER
logging.debug("OpenDayLight Control Adapter Starting...")
print("Welcome to 'OpenDayLight Control Adapter'")
    
# Falcon
logging.info("Starting server application")
app = falcon.API()

rest_interface = OpenDayLightCA_REST_NFFG()
rest_nffg_status = OpenDayLightCA_REST_NFFGStatus()
rest_user_auth = OpenDayLightCA_UserAuthentication()

app.add_route('/auth', rest_user_auth)
app.add_route('/NF-FG', rest_interface)
app.add_route('/NF-FG/{nffg_id}', rest_interface)
app.add_route('/NF-FG/status/{nffg_id}', rest_nffg_status)

logging.info("Falcon Successfully started")



    
    
