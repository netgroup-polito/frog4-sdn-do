'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''

import logging, falcon

# Configuration Parser
from odl_ca_core.config import Configuration

# REST Interface
from odl_ca_core.rest_interface import OpenDayLightCA_RestInterface

# Configuration
conf = Configuration()

# Log configuration
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s'
if conf.LOG_DEBUG is True:
    log_level = logging.DEBUG
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    sqlalchemy_log = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_log.setLevel(logging.WARNING)
elif conf.LOG_VERBOSE is True:
    log_level = logging.INFO
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
else:
    log_level = logging.WARNING
logging.basicConfig( filename="../"+conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')



# START OPENDAYLIGHT COMPONENT ADAPTER
logging.debug("OpenDayLight Component Adapter Starting...")
print "Welcome to 'OpenDayLight Component Adapter'"
    
# Falcon
logging.info("Starting server application")
app = falcon.API()

rest_interface = OpenDayLightCA_RestInterface()

app.add_route('/NF-FG', rest_interface)
app.add_route('/NF-FG/{nffg_id}', rest_interface)
#app.add_route('/NF-FG/status/{nffg_id}', rest_interface)


logging.info("Falcon Successfully started")





''''
#upper_layer_API = UpperLayerOrchestrator(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)
#template = TemplateAPI(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)
#yang = YANGAPI(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)

################################################################

#upper_layer_API = UpperLayerOrchestrator()


#in_file = open("/home/giacomo/eclipse_workspace/frog-orchestrator/graphs/odlCA_graphHe_Hydrogen.json","r")
#in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/graphs/odlCA_graphHe_Lithium.json","r")
#in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/graphs/odlCA_rm1.json","r")
in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/tests/graphs/odlCA_rm1.json","r")

# NF-FG File
nffg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)


# CONTROLLER
user = UserAuthentication().authenticateUserFromCredentials("demo_jolnet", "stack", "demo_jolnet")     
odlCA = OpenDayLightCA(user)

odlCA.NFFG_Delete(977)

odlCA.NFFG_Validate(nffg)
odlCA.NFFG_Put(nffg)

print("\n\nUpdating...")
in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/tests/graphs/odlCA_rm2.json","r")
nffg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)

odlCA.NFFG_Validate(nffg)
odlCA.NFFG_Put(nffg)
print("\n\nEnd update")
'''

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

'''



    
    
