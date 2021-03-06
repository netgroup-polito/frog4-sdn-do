'''
Created on Dic 7, 2015

@author: giacomoratta

This script test the main functions of the Network Controller Domain Orchestrator.
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
from do_core.config import Configuration

# SQL Session
from do_core.sql.sql_server import try_session

# Orchestrator Core
from do_core.user_authentication import UserAuthentication
from do_core.do import DO

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

# Clean All (starts automatically)
from scripts import clean_all

def put_json(filename):
    try:
        # Instantiate the domain orchestrator
        user = UserAuthentication().authenticateUserFromCredentials("admin", "admin", "admin_tenant")     
        NCDO = DO(user)

        # NF-FG File
        in_file = open("/abs/path/graphs/folder/"+filename,"r")
        nffg_file = json.loads(in_file.read())
        ValidateNF_FG().validate(nffg_file)
        nffg = NF_FG()
        nffg.parseDict(nffg_file)
        
        # Validate and Put
        NCDO.validate_nffg(nffg)
        NCDO.put_nffg(nffg)
        
    except Exception as ex:
        if hasattr(ex, 'message'):
            print(ex.message)
        elif hasattr(ex, 'args'):
            print(ex)
        else:
            print("Unknown exception")


# Test connection to database
try_session()

# START NETWORK CONTROLLER DOMAIN ORCHESTRATOR
logging.debug("Network Controller Domain Orchestrator Starting...")
print("Welcome to 'Network Controller Domain Orchestrator'")

put_json("hydrogen_invlan1a.json")

