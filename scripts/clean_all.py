'''
Delete all informations from the database.
Delete all installed flows from the switches.
Keep in the database user and tenant informations only.
'''
import os
os.environ.setdefault("FROG4_SDN_DO_CONF", "config/default-config.ini")
import logging
from do_core.sql.graph_session import GraphSession
from requests.exceptions import HTTPError
#from do_core.resource_description import ResourceDescription
from do_core.domain_information_manager import Messaging
from do_core.netmanager import NetManager
from do_core.config import Configuration

def do_core_clean_all():
    
    netmanager = NetManager()
    
    flowrules_separator = ", "
    deleted_flowrules = []
    notfound_flowrules = []
    
    logging.info("Starting cleaning database and switches...")
    external_flowrules = GraphSession().getAllExternalFlowrules()
    
    for ef in external_flowrules:
        try:            
            netmanager.deleteFlow(ef.switch_id, ef.internal_id)
            deleted_flowrules.append(ef.internal_id)
        
        except Exception as ex:
            if type(ex) is HTTPError and ex.response.status_code==404:
                #logging.debug("External flow "+ef.internal_id+" does not exist in the switch "+ef.switch_id+".")
                notfound_flowrules.append(ef.internal_id)
            else:
                logging.debug("Exception while deleting external flow "+ef.internal_id+" in the switch "+ef.switch_id+". "+ex.args[0])
    
    if len(deleted_flowrules)>0:
        logging.debug("Deleted flowrules: "+flowrules_separator.join(deleted_flowrules)+".")
    
    if len(notfound_flowrules)>0:
        logging.debug("Not found flowrules: "+flowrules_separator.join(notfound_flowrules)+".")
    
    GraphSession().cleanAll()
    logging.info("Cleaning database and switches completed!")
    
    #ResourceDescription().updateAll()
    #ResourceDescription().saveFile()
    #Messaging().PublishDomainConfig()
    logging.info("Resource description file updated!")
    
    print("Cleaning database and switches completed!")
    
Configuration().log_configuration()
do_core_clean_all()
