'''
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta

This script test the main functions of the OpenDayLight Control Adapter.
   1) Load configuration;
   2) load a json file with the NFFG to load;
   3) validate the NFFG;
   4) authenticate the "admin" user;
   5) delete a graph with id "977";
   6) put a new graph (with id "977", see the json file);
   7) put a graph with the same id (and we expect an update).
'''

import logging, json

# Configuration Parser
from odl_ca_core.config import Configuration

# Orchestrator Core
from odl_ca_core.user_authentication import UserAuthentication
from odl_ca_core.opendaylight_ca import OpenDayLightCA

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

# Configuration
conf = Configuration()
conf.log_configuration()



# START OPENDAYLIGHT CONTROL ADAPTER
logging.debug("OpenDayLight Control Adapter Starting...")
print "Welcome to 'OpenDayLight Control Adapter'"
    

# NF-FG File
in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/tests/graphs/odlCA_put2.json","r")
nffg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)


# Instantiate the control adapter
user = UserAuthentication().authenticateUserFromCredentials("admin", "admin", "admin_tenant")     
odlCA = OpenDayLightCA(user)

# Delete
try:
    odlCA.NFFG_Delete(977)
except Exception as ex:
    print ex.message
#quit()


# Validate and Put
odlCA.NFFG_Validate(nffg)
odlCA.NFFG_Put(nffg)


# NF-FG File (with updates) 
in_file = open("/home/giacomo/eclipse_workspace/frog4-ODL-CA/tests/graphs/odlCA_put2.json","r")
nffg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)

# Validate and Put (update expected)
print("Updating...")
odlCA.NFFG_Validate(nffg)
odlCA.NFFG_Put(nffg)
print("End update")



    
    
