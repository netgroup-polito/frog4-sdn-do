'''
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta

This script test has to be called via gunicorn.
Write in the shell:
    $ gunicorn -b 0.0.0.0:9000 -t 500 main2:app

Otherwise, make a python script with this two rows:
    from subprocess import call
    call("gunicorn -b 0.0.0.0:9000 -t 500 main2:app", shell=True)

Script phases:
   1) Load configuration;
   2) start falcon web framework;
   3) add api paths.
'''

import logging, falcon

# Configuration Parser
from odl_ca_core.config import Configuration

# Create database
from odl_ca_core.sql.sql_server import session_create_database
from odl_ca_core.user_authentication import UserAuthentication
# REST Interface
from odl_ca_core.rest_interface import OpenDayLightCA_REST_NFFG, OpenDayLightCA_REST_NFFGStatus, OpenDayLightCA_UserAuthentication

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
rest_nffg_status = OpenDayLightCA_REST_NFFGStatus()
rest_user_auth = OpenDayLightCA_UserAuthentication()

app.add_route('/auth', rest_user_auth)
app.add_route('/NF-FG', rest_interface)
app.add_route('/NF-FG/{nffg_id}', rest_interface)
app.add_route('/NF-FG/status/{nffg_id}', rest_nffg_status)

logging.info("Falcon Successfully started")


'''

TODO
 
[ 1 ]
- eliminare tabella endpoint_resource (verificare a che serve)
- cambiare nomi dei campi di tabelle nel db in nomi piu' esplicativi
- sistemare i *Model in graph_session.py
- creare un db.sql aggiornato


- definire interfaccia DOUBLEDECKER
- pulire ulteriormente il database

- check TODO: remove


[ DOMANDE ]
- campi tabelle db
- eccezioni manifest, validator, ecc.
- quali eccezioni gestire in rest_interface.py ?

'''



    
    
