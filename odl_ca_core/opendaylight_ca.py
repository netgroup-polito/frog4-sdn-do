'''
@author: fabiomignini
@author: vida
@author: giacomoratta
'''

from __future__ import division
from __builtin__ import str
import logging, json

from nffg_library.nffg import FlowRule

from odl_ca_core.sql.graph_session import GraphSession

from odl_ca_core.config import Configuration
from odl_ca_core.exception import sessionNotFound, GraphError
from odl_ca_core.odl_rest import ODL_Rest
from odl_ca_core.resources import Action, Match, Flow, ProfileGraph, Endpoint
from odl_ca_core.netgraph import NetGraph

class OpenDayLightCA(object):

    def __init__(self, user_data):
        
        self.nffg = None
        self.session_id = None
        self.user_data = user_data
        '''
        Fields:
         - user_data.username
         - user_data.password
         - user_data.tenant
        '''
        
        # Dati ODL
        if(False):
            self.odlendpoint = "http://127.0.0.1:8080"
            self.odlversion = "Hydrogen"
        else:
            self.odlendpoint = "http://127.0.0.1:8181"
            self.odlversion = "Lithium"
        self.odlusername = "admin"
        self.odlpassword = "admin"
        
        # NetGraph
        self.netgraph = NetGraph(self.odlversion, self.odlendpoint, self.odlusername, self.odlpassword)
    
    
    
    def put(self, nffg):
        '''
        Manage the request of NF-FG instantiation
        '''
        logging.debug("Put NF-FG: put from user "+self.user_data.username+" on tenant "+self.user_data.tenant)
        
        # Check if the NF-FG is already instantiated
        session_id = self.status(nffg.id)
        if session_id is not None:
            logging.debug("Put NF-FG: already instantiated, trying to update it")
            session_id = self.update(nffg, session_id)
        
        # Instantiate a new NF-FG
        else:
            try:
                session_id = GraphSession().addNFFG(nffg, self.user_data.getUserID())
                logging.debug("Put NF-FG: instantiating a new nffg: " + nffg.getJSON(True))
                
                # Profile graph for ODL functions
                profile_graph = self.buildProfileGraph(nffg)
                
                # Write latest info in the database and send all the flow rules to ODL
                self.opendaylightFlowsInstantiation(profile_graph, nffg)
                
                logging.debug("Put NF-FG: session " + profile_graph.id + " correctly instantiated!")

            except Exception as ex:
                logging.error(ex.message)
                logging.exception(ex)
                GraphSession().delete_graph(session_id)
                GraphSession().setErrorStatus(session_id)
                raise ex
        
        GraphSession().updateStatus(session_id, 'complete')                                
        return session_id

    
    
    def update(self, new_nffg, session_id):

        if session_id is None:
            # Throws sessionNotFound exception
            session = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), new_nffg.id, error_aware=True)
            session_id = session.id
        
        # Set session_id in the new NFFG
        new_nffg.db_id = session_id
        
        logging.debug("Update NF-FG: updating session "+session_id+" from user "+self.user_data.username+" on tenant "+self.user_data.tenant)
        GraphSession().updateStatus(session_id, 'updating')

        # Get the old NFFG
        old_nffg = GraphSession().get_nffg(session_id)
        logging.debug("Update NF-FG: the old session: "+old_nffg.getJSON())
        
        # TODO: remove or integrate remote_graph and remote_endpoint

        try:
            updated_nffg = old_nffg.diff(new_nffg)
            updated_nffg.db_id = session_id
            logging.debug("Update NF-FG: coming updates: "+updated_nffg.getJSON(True))            
            
            # Delete useless endpoints and flowrules 
            self.opendaylightFlowsControlledDeletion(updated_nffg)
            
            # Update database and send flowrules to ODL
            GraphSession().updateNFFG(updated_nffg, self.session_id)
            profile_graph = self.buildProfileGraph(updated_nffg)
            self.opendaylightFlowsInstantiation(profile_graph, updated_nffg)
            
            logging.debug("Update NF-FG: session " + session_id + " correctly updated!")
            
        except Exception as ex:
            logging.error("Update NF-FG: "+ex.message)
            logging.exception("Update NF-FG: "+ex)
            # TODO: discuss... delete the graph when an error occur in this phase?
            #GraphSession().delete_graph(session_id)
            #GraphSession().setErrorStatus(session_id)
            raise ex
        
        GraphSession().updateStatus(session_id, 'complete')
        return session_id
    
    
    
    def delete(self, nffg_id):        
        session = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg_id, error_aware=False)
        logging.debug("Deleting session: "+str(session.id))

        instantiated_nffg = GraphSession().get_nffg(session.id)
        logging.debug('NF-FG that we are going to delete: '+instantiated_nffg.getJSON())
            
        # De-instantiate profile
        orchestrator = OpenDayLightCA(session.id, self.user_data)

        try:
            orchestrator.deinstantiateProfile(instantiated_nffg)
        except Exception as ex:
            logging.exception(ex)
            raise ex
            
        logging.debug('Session deleted: '+str(session.id))     
        GraphSession().delete_graph(session.id)
        GraphSession().set_ended(session.id)



    def get(self, nffg_id):
        # Throws sessionNotFound exception
        session = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg_id, error_aware=False)
        logging.debug("Getting session: "+str(session.id))
        return GraphSession().get_nffg(session.id).getJSON()



    def status(self, nffg_id):
        try:
            session_ref = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(),nffg_id,error_aware=True)
            logging.debug("Graph status: "+str(session_ref.status))
            return session_ref.id
        except sessionNotFound:
            return None
    
    
    
    def validate(self, nffg):
        if len(nffg.vnfs)>0:
            logging.debug("NFFG: presence of 'VNFs'. This CA does not process this information.")
        
        for ep in nffg.end_points:
            if(ep.remote_endpoint_id is not None):
                logging.debug("NFFG: presence of 'end-points.remote_endpoint_id'. This CA does not process this information.")
            #if(ep.remote_ip is not None):
            #    logging.debug("NFFG: presence of 'end-points.remote-ip'. This CA does not process this information.")
            if(ep.type <> "interface"):
                logging.debug("NFFG: 'end-points.type' must be 'interface'.")
            
            
    
    def buildProfileGraph(self, nffg):
        '''
        Create a ProfileGraph with the flowrules and endpoint specified in nffg.
        Args:
            nffg:
                Object of the Class Common.NF_FG.nffg.NF_FG
        Return:
            Object of the Class odl_ca_core.resources.ProfileGraph
        '''
        profile_graph = ProfileGraph()
        profile_graph.setId(nffg.db_id)

        for endpoint in nffg.end_points:
            
            if endpoint.status is None:
                status = "new"
            else:
                status = endpoint.status

            # TODO: remove or integrate 'remote_endpoint' code
            
            ep = Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.switch_id, endpoint.interface, status)
            profile_graph.addEndpoint(ep)
        
        for flowrule in nffg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            profile_graph.addFlowrule(flowrule)
                  
        return profile_graph        
            
            
            