'''
Delete all informations from the database.
Delete all installed flows from the switches.
Keep in the database user and tenant informations only.
'''

import logging
from odl_do.config import Configuration
from odl_do.odl_rest import ODL_Rest
from odl_do.sql.graph_session import GraphSession
from requests.exceptions import HTTPError
from odl_do.resource_description import ResourceDescription


def odl_do_clean_all():
    flowrules_separator = ", "
    deleted_flowrules = []
    notfound_flowrules = []
    
    logging.info("Starting cleaning database and switches...")
    external_flowrules = GraphSession().getAllExternalFlowrules()
    
    for ef in external_flowrules:
        try:
            ODL_Rest(Configuration().ODL_VERSION).deleteFlow(Configuration().ODL_ENDPOINT, 
                                                             Configuration().ODL_USERNAME, 
                                                             Configuration().ODL_PASSWORD, 
                                                             ef.switch_id, ef.internal_id)
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
    
    ResourceDescription().updateTrunkVlanIDs()
    ResourceDescription().saveFile()
    logging.info("Resource description file updated!")
    
    print("Cleaning database and switches completed!")
    

odl_do_clean_all()
