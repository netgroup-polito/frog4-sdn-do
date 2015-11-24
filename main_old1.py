'''
Created on Oct 1, 2014

@author: fabiomignini
'''

#import falcon
#from orchestrator_core.orchestrator import UpperLayerOrchestrator, TemplateAPI, YANGAPI, TemplateAPILocation, NFFGStatus


import logging, json

# Configuration Parser
from orchestrator_core.config import Configuration

# Orchestrator Core
from orchestrator_core.userAuthentication import UserAuthentication
from orchestrator_core.controller import UpperLayerOrchestratorController

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG



conf = Configuration()

# set log level
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

#format = '%(asctime)s %(filename)s %(funcName)s %(levelname)s %(message)s'
log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s'

logging.basicConfig( filename=conf.LOG_FILE, level=log_level, format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
logging.debug("Orchestrator Starting")


print "Welcome to the UN orchestrator_core"
    

# Falcon starts
#app = falcon.API()
logging.info("Starting Orchestration Server application")

#upper_layer_API = UpperLayerOrchestrator(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)
#template = TemplateAPI(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)
#yang = YANGAPI(conf.AUTH_SERVER,conf.ORCH_USERNAME,conf.ORCH_PASSWORD,conf.ORCH_TENANT)

################################################################

#upper_layer_API = UpperLayerOrchestrator()

user = UserAuthentication().authenticateUserFromCredentials("demo_jolnet", "stack", "demo_jolnet")     
controller = UpperLayerOrchestratorController(user)




#in_file = open("/home/giacomo/eclipse_workspace/frog-orchestrator/graphs/odlCA_graphHe_Hydrogen.json","r")
in_file = open("/home/giacomo/eclipse_workspace/frog-orchestrator/graphs/odlCA_graphHe_Lithium.json","r")

nf_fg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nf_fg_file)
nf_fg = NF_FG()
nf_fg.parseDict(nf_fg_file)

controller.delete(977)
controller.put(nf_fg)






    
    
