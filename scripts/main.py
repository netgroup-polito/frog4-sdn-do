'''
Created on Dic 7, 2015

@author: fabiomignini
@author: giacomoratta

This script test the main functions of the OpenDayLight Domain Orchestrator.
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
from odl_do.config import Configuration

# SQL Session
from odl_do.sql.sql_server import try_session

# Orchestrator Core
from odl_do.user_authentication import UserAuthentication
from odl_do.opendaylight_do import OpenDayLightDO

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

# Clean All (starts automatically)
import clean_all

def put_json(odlDO, filename):
    try:
        # NF-FG File
        in_file = open("/home/giacomo/eclipse_workspace/frog4-odl-do/tests/graphs/"+filename,"r")
        nffg_file = json.loads(in_file.read())
        ValidateNF_FG().validate(nffg_file)
        nffg = NF_FG()
        nffg.parseDict(nffg_file)
        
        # Validate and Put
        odlDO.NFFG_Validate(nffg)
        odlDO.NFFG_Put(nffg)
        
    except Exception as ex:
        if hasattr(ex, 'message'):
            print(ex.message)
        elif hasattr(ex, 'args'):
            print(ex)
        else:
            print("Unknown exception")



# Configuration
conf = Configuration()
conf.log_configuration()

# Test connection to database
try_session()

# START OPENDAYLIGHT DOMAIN ORCHESTRATOR
logging.debug("OpenDayLight Domain Orchestrator Starting...")
print("Welcome to 'OpenDayLight Domain Orchestrator'")

# Instantiate the domain orchestrator
user = UserAuthentication().authenticateUserFromCredentials("admin", "admin", "admin_tenant")     
odlDO = OpenDayLightDO(user)

put_json(odlDO,"hydrogen_invlan1a.json")

'''
put_json(odlDO,"prog1/invlan1a.json")
put_json(odlDO,"prog1/invlan1b.json")
put_json(odlDO,"prog1/invlan1c.json")
put_json(odlDO,"prog1/invlan1d.json")
put_json(odlDO,"prog1/invlan1e.json")
put_json(odlDO,"prog1/invlan1f.json")
put_json(odlDO,"prog1/invlan1g.json")
put_json(odlDO,"prog1/invlan1h.json")
put_json(odlDO,"prog1/invlan1i.json")
put_json(odlDO,"prog1/invlan1l.json")
'''
    
