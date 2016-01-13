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

# Configuration
conf = Configuration()
conf.log_configuration()

# Test connection to database
try_session()

conf = Configuration()

# START OPENDAYLIGHT DOMAIN ORCHESTRATOR
logging.debug("OpenDayLight Domain Orchestrator Starting...")
print("Welcome to 'OpenDayLight Domain Orchestrator'")


# Instantiate the domain orchestrator
user = UserAuthentication().authenticateUserFromCredentials("admin", "admin", "admin_tenant")     
odlDO = OpenDayLightDO(user)



# Delete
deldel=False
deldel=True
if deldel: 
    try:
        #print(odlDO.NFFG_Get(977))
        odlDO.NFFG_Delete(977)
    except Exception as ex:
        print(ex)
    try:
        odlDO.NFFG_Delete(988)
    except Exception as ex:
        print(ex)
    #quit()
    
# NF-FG File
in_file = open("/home/giacomo/eclipse_workspace/frog4-odl-do/tests/graphs/test1.json","r")
try:
    nffg_file = json.loads(in_file.read())
except ValueError as err:
    raise err
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)

# Validate and Put
odlDO.NFFG_Validate(nffg)
odlDO.NFFG_Put(nffg)

quit()

# NF-FG File
in_file = open("/home/giacomo/eclipse_workspace/frog4-odl-do/tests/graphs/odlCA_invlan2a.json","r")
nffg_file = json.loads(in_file.read())
ValidateNF_FG().validate(nffg_file)
nffg = NF_FG()
nffg.parseDict(nffg_file)

# Validate and Put
odlDO.NFFG_Validate(nffg)
odlDO.NFFG_Put(nffg)

quit()

# Validate and Put (update expected)
print("Updating...")
odlDO.NFFG_Validate(nffg)
odlDO.NFFG_Put(nffg)
print("End update")


'''

DOUBLE DECKER
    1) clonare DD da gitlab;
    2) introdurre fix di Stefano;
    3) specificare la directory DD in gitignore 
    3) usare dd_server.py

FLOW RULES "simili"
    Gestire flow rules con match uguale!


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


    
