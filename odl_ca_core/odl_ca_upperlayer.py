'''
@authors: fabiomignini
@author: giacomoratta
'''

from __future__ import division
import logging

from odl_ca_core.config import Configuration
from odl_ca_core.sql.graph2 import Graph2
from odl_ca_core.odl_ca import OpenDayLight_CA
from odl_ca_core.exception import sessionNotFound

DEBUG_MODE = Configuration().DEBUG_MODE


class UpperLayer_ODL_CA(object):

    def __init__(self, user_data):
        
        self.user_data = user_data
        '''
        Fields:
         - user_data.username
         - user_data.password
         - user_data.tenant
        '''
    
    
    
    def put(self, nffg):
        """
        Manage the request of NF-FG instantiation
        """
        session_id = None
        logging.debug('Put from user '+self.user_data.username+" of tenant "+self.user_data.tenant)
        
        # NF-FG already instantiated
        if self.checkNFFGStatus(nffg.id) is True:
            logging.debug('NF-FG already instantiated, trying to update it')
            session_id = self.update(nffg)
            logging.debug('Update completed')
        
        else:
            try:
                session_id = Graph2().addNFFG(nffg, self.user_data.getUserID())
                logging.debug("Added NF-FG: "+nffg.getJSON())
                
                logging.info('Call CA to instantiate NF-FG')
                orchestrator = OpenDayLight_CA(nffg.db_id, self.user_data)               
                orchestrator.instantiateProfile(nffg)
                
                logging.debug('NF-FG instantiated') 
                Graph2().updateSessionNode(session_id)

            except Exception as ex:
                logging.exception(ex)
                Graph2().delete_graph(nffg.db_id)
                Graph2().set_error(session_id)
                raise ex
        
        Graph2().updateStatus(session_id, 'complete')
                                
        return session_id

    
    
    def update(self, nffg):
        # Throws sessionNotFound exception
        session = Graph2().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg.id, error_aware=True)
        Graph2().updateStatus(session.session_id, 'updating')
            
        old_nffg = Graph2().get_nffg(session.session_id)
        logging.debug('NF-FG that has to be updated: '+old_nffg.getJSON())

        logging.info('Call CA to update NF-FG')
        orchestrator = OpenDayLight_CA(old_nffg.db_id, self.user_data) 
        
        # TODO: remote graph
        
        # If the orchestrator have to connect two graphs in different nodes,
        # the end-points must be characterized to allow a connection between nodes
        #remote_nffgs_dict = self.analizeRemoteConnection(nffg, new_node)
        
        # If needed, update the remote graph
        #self.updateRemoteGraph(remote_nffgs_dict)

        # Update the nffg
        try:
            nffg.db_id = old_nffg.db_id # nffg.db_id = graph.session_id
            orchestrator.updateProfile(nffg, old_nffg)
        except Exception as ex:
            logging.exception(ex)
            raise ex
        
        Graph2().updateStatus(session.session_id, 'complete')
        Graph2().updateSessionNode(session.session_id)
        return session.session_id
    
    
    
    def delete(self, nffg_id):        
        session = Graph2().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg_id, error_aware=False)
        logging.debug("Deleting session: "+str(session.session_id))

        instantiated_nffg = Graph2().get_nffg(session.session_id)
        logging.debug('NF-FG that we are going to delete: '+instantiated_nffg.getJSON())
            
        # De-instantiate profile
        orchestrator = OpenDayLight_CA(session.session_id, self.user_data)

        try:
            orchestrator.deinstantiateProfile(instantiated_nffg)
        except Exception as ex:
            logging.exception(ex)
            raise ex
            
        logging.debug('Session deleted: '+str(session.session_id))     
        Graph2().delete_graph(session.session_id)
        Graph2().set_ended(session.session_id)



    def get(self, nffg_id):
        # Throws sessionNotFound exception
        session = Graph2().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg_id, error_aware=False)
        
        logging.debug("Getting session: "+str(session.session_id))
        return Graph2().get_nffg(session.session_id).getJSON()



    def checkNFFGStatus(self, nffg_id):
        try:
            session_ref = Graph2().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(),nffg_id)
            logging.debug("Graph status: "+str(session_ref.status))
            return True
        except sessionNotFound:
            return False
        
        if DEBUG_MODE is True:
            return True
        
        return False