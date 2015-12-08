'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''

import logging, falcon

# Configuration Parser
from odl_ca_core.config import Configuration

# REST Interface
from odl_ca_core.rest_interface import OpenDayLightCA_REST_NFFG, OpenDayLightCA_REST_NFFGStatus

# Configuration
conf = Configuration()
conf.log_configuration()




# START OPENDAYLIGHT COMPONENT ADAPTER
logging.debug("OpenDayLight Component Adapter Starting...")
print "Welcome to 'OpenDayLight Component Adapter'"
    
# Falcon
logging.info("Starting server application")
app = falcon.API()

rest_interface = OpenDayLightCA_REST_NFFG()
nffg_status = OpenDayLightCA_REST_NFFGStatus()

app.add_route('/NF-FG', rest_interface)
app.add_route('/NF-FG/{nffg_id}', rest_interface)
app.add_route('/NF-FG/status/{nffg_id}', nffg_status)

logging.info("Falcon Successfully started")


'''
 
[ 1 ]
- eliminare tabella endpoint_resource (verificare a che serve)
- cambiare nomi dei campi di tabelle nel db in nomi piu' esplicativi
- sistemare i *Model in graph_session.py
- creare un db.sql aggiornato


[ 5 ]
passare a sqlite
- sqlalchemy engine 'sqlite'
- da phpmyadmin a phpliteadmin


- definire interfaccia REST
- definire interfaccia DOUBLEDECKER
- pulire ulteriormente il database

- check TODO: remove


[ DOMANDE ]
- campi tabelle db
- eccezioni manifest, validator, ecc.

'''



    
    
