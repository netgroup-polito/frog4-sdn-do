'''
Created on Oct 1, 2014

@author: fabiomignini
'''

#import falcon
#from odl_ca_core.orchestrator import UpperLayerOrchestrator, TemplateAPI, YANGAPI, TemplateAPILocation, NFFGStatus


import logging, json

# Configuration Parser
from odl_ca_core.config import Configuration

# Orchestrator Core
from odl_ca_core.user_authentication import UserAuthentication
from odl_ca_core.odl_ca_upperlayer import UpperLayer_ODL_CA

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG



conf = Configuration()



# LOG LEVEL
if conf.DEBUG is True:
    log_level = logging.DEBUG
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
    sqlalchemy_log = logging.getLogger('sqlalchemy.engine')
    sqlalchemy_log.setLevel(logging.WARNING)
elif conf.VERBOSE is True:
    log_level = logging.INFO
    requests_log = logging.getLogger("requests")
    requests_log.setLevel(logging.WARNING)
else:
    log_level = logging.WARNING

# LOG FORMAT
#format = '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s'
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s'

# START LOGGING
logging.basicConfig( filename="../"+conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Orchestrator Starting")


print "Welcome to 'OpenDayLight Component Adapter'"
    

# Falcon starts
#app = falcon.API()
logging.info("Starting Orchestration Server application")

#upper_layer_API = UpperLayerOrchestrator(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)
#template = TemplateAPI(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)
#yang = YANGAPI(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)

################################################################

#upper_layer_API = UpperLayerOrchestrator()


#in_file = open("/home/giacomo/eclipse_workspace/frog-orchestrator/graphs/odlCA_graphHe_Hydrogen.json","r")
#in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/graphs/odlCA_graphHe_Lithium.json","r")
#in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/graphs/odlCA_rm1.json","r")
in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/graphs/odlCA_rm2.json","r")

# NF-FG File
nffg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)


# CONTROLLER
user = UserAuthentication().authenticateUserFromCredentials("demo_jolnet", "stack", "demo_jolnet")     
controller = UpperLayer_ODL_CA(user)
controller.validate(nffg)
controller.delete(977)
controller.put(nffg)

print("\n\nUpdating...")
#controller.put(nffg)
print("\n\nEnd update")


'''
 
[ 1 ]
- eliminare il nome "graph_id" da tutte le tabelle in favore di "session_id"

[ 2 ]
provare endpoint remoti e creazione di endpoint_resource con resource_type="flowrule"
SERVONO GLI ENDPOINT REMOTI in questo caso???


[ 4 ]
eliminare informazioni inutili da orchestrator.conf e classe Configuration()


[ 5 ]
passare a sqlite
- sqlalchemy engine 'sqlite'
- da phpmyadmin a phpliteadmin


- definire interfaccia REST
- definire interfaccia DOUBLEDECKER
- pulire ulteriormente il database
- eliminare qualsiasi riferimento al vecchio "orchestrator", "jolnet", ecc.

- check NOTUSED
- check TODO: remove

'''



    
    
