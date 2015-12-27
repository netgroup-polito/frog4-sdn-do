'''
Created on Dic 21, 2015

@author: giacomoratta

This script tests gunicorn async workers 

This script test has to be called via gunicorn.
Write in the shell:
    $ gunicorn -b 0.0.0.0:9000 -t 500 main3:app

Otherwise, make a python script with this two rows:
    from subprocess import call
    call("gunicorn -b 0.0.0.0:9000 -t 500 main3:app", shell=True)

Script phases:
   1) Load configuration;
   2) start falcon web framework;
   3) add api paths.
'''

import logging, falcon

# Configuration Parser
from odl_ca_core.config import Configuration

# REST Interface
from odl_ca_core.rest_interface import OpenDayLightCA_REST_NFFG, OpenDayLightCA_REST_NFFGStatus

# Configuration
conf = Configuration()
conf.log_configuration()



# START OPENDAYLIGHT CONTROL ADAPTER
logging.debug("OpenDayLight Control Adapter Starting...")
print("Welcome to 'OpenDayLight Control Adapter'")
    
# Falcon
logging.info("Starting server application")
app = falcon.API()

rest_interface = OpenDayLightCA_REST_NFFG()
nffg_status = OpenDayLightCA_REST_NFFGStatus()

app.add_route('/NF-FG', rest_interface)
app.add_route('/NF-FG/{nffg_id}', rest_interface)
app.add_route('/NF-FG/status/{nffg_id}', nffg_status)

logging.info("Falcon Successfully started")