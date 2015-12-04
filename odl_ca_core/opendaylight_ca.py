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

#from odl_ca_core.config import Configuration
from odl_ca_core.exception import sessionNotFound, GraphError
from odl_ca_core.odl_rest import ODL_Rest
from odl_ca_core.resources import Action, Match, Flow, ProfileGraph, Endpoint
from odl_ca_core.netgraph import NetGraph

class OpenDayLightCA(object):

    def __init__(self, user_data):
        
        # TODO: use configuration
        # TODO: change names of odl functions and sub-functions
        
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
    
    
    
    def NFFG_Put(self, nffg):
        '''
        Manage the request of NF-FG instantiation
        '''
        logging.debug("Put NF-FG: put from user "+self.user_data.username+" on tenant "+self.user_data.tenant)
        
        # Check if the NF-FG is already instantiated
        session_id = self.NFFG_Status(nffg.id)
        if session_id is not None:
            logging.debug("Put NF-FG: already instantiated, trying to update it")
            session_id = self.NFFG_Update(nffg, session_id)
        
        # Instantiate a new NF-FG
        else:
            try:
                session_id = GraphSession().addNFFG(nffg, self.user_data.getUserID())
                logging.debug("Put NF-FG: instantiating a new nffg: " + nffg.getJSON(True))
                
                # Profile graph for ODL functions
                profile_graph = self.ProfileGraph_BuildFromNFFG(nffg)
                
                # Write latest info in the database and send all the flow rules to ODL
                self.opendaylightFlowsInstantiation(profile_graph)
                
                logging.debug("Put NF-FG: session " + profile_graph.id + " correctly instantiated!")

            except Exception as ex:
                logging.error(ex.message)
                logging.exception(ex)
                GraphSession().delete_graph(session_id)
                GraphSession().setErrorStatus(session_id)
                raise ex
        
        GraphSession().updateStatus(session_id, 'complete')                                
        return session_id

    
    
    def NFFG_Update(self, new_nffg, session_id):

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
            profile_graph = self.ProfileGraph_BuildFromNFFG(updated_nffg)
            self.opendaylightFlowsInstantiation(profile_graph)
            
            logging.debug("Update NF-FG: session " + session_id + " correctly updated!")
            
        except Exception as ex:
            logging.error("Update NF-FG: "+ex.message)
            logging.exception("Update NF-FG: "+ex)
            # TODO: discuss... delete the graph when an error occurs in this phase?
            #GraphSession().delete_graph(session_id)
            #GraphSession().setErrorStatus(session_id)
            raise ex
        
        GraphSession().updateStatus(session_id, 'complete')
        return session_id
    
    
    
    def NFFG_Delete(self, nffg_id):        
        session = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg_id, error_aware=False)
        logging.debug("Delete NF-FG: deleting session "+str(session.id))

        instantiated_nffg = GraphSession().get_nffg(session.id)
        logging.debug("Delete NF-FG: we are going to delete: "+instantiated_nffg.getJSON())
    
        try:
            self.opendaylightFlowsDeletion(session.id)
            logging.debug("Delete NF-FG: session " + session.id + " correctly deleted!")
            
        except Exception as ex:
            logging.error("Delete NF-FG: "+ex.message)
            logging.exception("Delete NF-FG: "+ex)
            #raise ex - no raise because we need to delete the session in any case
        GraphSession().delete_graph(session.id)
        GraphSession().set_ended(session.id)



    def NFFG_Get(self, nffg_id):
        # Throws sessionNotFound exception
        session = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(), nffg_id, error_aware=False)
        logging.debug("Getting session: "+str(session.id))
        return GraphSession().get_nffg(session.id).getJSON()



    def NFFG_Status(self, nffg_id):
        try:
            session_ref = GraphSession().get_active_user_session_by_nf_fg_id(self.user_data.getUserID(),nffg_id,error_aware=True)
            logging.debug("Graph status: "+str(session_ref.status))
            return session_ref.id
        except sessionNotFound:
            return None
    
    
    
    def NFFG_Validate(self, nffg):
        if len(nffg.vnfs)>0:
            logging.debug("NFFG: presence of 'VNFs'. This CA does not process this information.")
        
        for ep in nffg.end_points:
            if(ep.remote_endpoint_id is not None):
                logging.debug("NFFG: presence of 'end-points.remote_endpoint_id'. This CA does not process this information.")
            #if(ep.remote_ip is not None):
            #    logging.debug("NFFG: presence of 'end-points.remote-ip'. This CA does not process this information.")
            if(ep.type <> "interface"):
                logging.debug("NFFG: 'end-points.type' must be 'interface'.")
            
            
    
    def ProfileGraph_BuildFromNFFG(self, nffg):
        '''
        Create a ProfileGraph with the flowrules and endpoints specified in nffg.
        Args:
            nffg:
                Object of the Class Common.NF_FG.nffg.NF_FG
        Return:
            Object of the Class odl_ca_core.resources.ProfileGraph
        '''
        profile_graph = ProfileGraph()
        profile_graph.setId(nffg.db_id) #session_id

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
    
    
    
    
    def opendaylightFlowsInstantiation(self, profile_graph):        
        
        # profile_graph.id has the session_id
        
        # Create the endpoints
        for endpoint in profile_graph.endpoints.values():
            if endpoint.status == "new":
                
                # TODO: remove or integrate remote_graph and remote_endpoint
                
                # TODO: move setEndpointLocation to addNFFG and updateNFFG;
                #       ...this function regards GraphSession and should not be here.
                GraphSession().setEndpointLocation(profile_graph.id, endpoint.id, endpoint.interface)

        # Create and push the flowrules
        for flowrule in profile_graph.flowrules.values():
            if flowrule.status =='new':
                
                #TODO: check priority
                
                if flowrule.match is not None:
                    if flowrule.match.port_in is not None:
                        
                        tmp1 = flowrule.match.port_in.split(':')
                        port1_type = tmp1[0]
                        port1_id = tmp1[1]
                        
                        if port1_type == 'endpoint':
                            endp1 = profile_graph.endpoints[port1_id]
                            if endp1.type == 'interface':        
                                self.processFlowrule(endp1, flowrule, profile_graph)
                                
    
    
    def opendaylightFlowsDeletion(self, session_id):       
        
        #Delete every flow from ODL
        
        flows = GraphSession().getFlowRules(session_id)
        for flow in flows:
            if flow.type == "external" and flow.status == "complete":
                ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow.switch_id, flow.graph_flow_rule_id)
                
         
            
    def opendaylightFlowsControlledDeletion(self, updated_nffg):
        
        # updated_nffg.db_id has the session_id
        
        # Delete the endpoints 'to_be_deleted'
        for endpoint in updated_nffg.end_points[:]:
            if endpoint.status == 'to_be_deleted':
                
                # TODO: remove or integrate remote_graph, remote_endpoint, endpoint_resource "flowrule", and graph_connection
                
                # Delete endpoints and all resourcess associated to it.
                GraphSession().deleteEndpoint(endpoint.id, updated_nffg.db_id)
                GraphSession().deleteEndpointResourceAndResources(endpoint.db_id)
                
                updated_nffg.end_points.remove(endpoint)  
        
        # Delete the flowrules 'to_be_deleted'              
        for flowrule in updated_nffg.flow_rules[:]:
            if flowrule.status == 'to_be_deleted' and flowrule.type != 'external':
                
                # Get and delete the flow rules with the same flow.internal_id,
                # which are the flow rules effectively pushed in ODL.
                flows = GraphSession().getFlowRules(updated_nffg.db_id)
                for flow in flows:
                    if flow.type == "external" and flow.status == "complete" and flow.internal_id == flowrule.id:
                        ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow.switch_id, flow.graph_flow_rule_id)
                        GraphSession().deleteFlowRule(flow.id)
                
                # Finally, delete the main flow rule (that written in nffg.json)
                GraphSession().deleteFlowRule(flowrule.db_id)
                updated_nffg.flow_rules.remove(flowrule)
                
        
            
            
            
    '''
    ######################################################################################################
    #########################    Interactions with OpenDaylight              #############################
    ######################################################################################################
    '''
    
    def processFlowrule(self, endpoint1, flowrule, profile_graph):
        
        #Process a flow rule written in the section "big switch" of a nffg json.
        
        # profile_graph.id has the session_id
        match1 = Match(flowrule.match)
        match2 = None
        actions1 = []
        actions2 = []
        switch1 = None
        switch2 = None
        flowname1 = None
        flowname2 = None        
        
        nodes_path = None
        nodes_path_flag = None
        print "\n\n\nprocessFlowrule"
        
        # Add "Drop" flow rules only, and return
        for act in flowrule.actions:
            if act.drop is True:
                action = Action(act)
                actions = [action]
                match1.setInputMatch(endpoint1.interface)
                flowname = str(flowrule.id)
                flowj = Flow("flowrule", flowname, 0, flowrule.priority, True, 0, 0, actions, match1)        
                json_req = flowj.getJSON(self.odlversion, endpoint1.switch_id)
                ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, endpoint1.switch_id, flowname)
                
                flow_rule = FlowRule(_id=flowname,node_id=endpoint1.switch_id,_type='external', status='complete',priority=flowrule.priority, internal_id=flowrule.id)  
                GraphSession().addFlowRule(profile_graph.id, endpoint1.switch_id, flow_rule, None)
                return  
        
        for act in flowrule.actions:
            if act.output is not None:
                
                tmp2 = act.output.split(':')
                port2_type = tmp2[0]
                port2_id = tmp2[1]
                if port2_type == 'endpoint': 
                    endpoint2 = profile_graph.endpoints[port2_id]
                                
                    if endpoint1.switch_id == endpoint2.switch_id:
                        if endpoint1.interface == endpoint2.interface:
                            raise GraphError("Flowrule "+flowrule.id+" is wrong: endpoints are overlapping")
                        else:
                            action1 = Action(act)
                            action1.setOutputAction(endpoint2.interface, 65535)
                            actions1.append(action1)

                            match1.setInputMatch(endpoint1.interface)
                            
                            flowname1 = str(flowrule.id)
                            switch1 = endpoint1.switch_id              
                    else:
                        port12,port21 = self.getLinkPortsBetweenSwitches(endpoint1.switch_id, endpoint2.switch_id)       
                        if port12 is not None and port21 is not None:

                            if endpoint1.interface != port12 and endpoint2.interface != port21:
                                # endpoints are not on the link: 2 flows 
                                action1 = Action(act)
                                action1.setOutputAction(port12, 65535)
                                actions1.append(action1)
                                
                                match1.setInputMatch(endpoint1.interface)
                                
                                flowname1 = str(flowrule.id) + str(1) 
                                switch1 = endpoint1.switch_id

                                # second flow
                                action2 = Action()
                                action2.setOutputAction(endpoint2.interface, 65535)
                                actions2 = [action2]
                                match2 = Match()
                                match2.setInputMatch(port21) 
                                
                                #second_flow = True
                                flowname2 = str(flowrule.id) + str(2)
                                switch2 = endpoint2.switch_id
                                
                            elif endpoint1.interface != port12 and endpoint2.interface == port21:
                                #flow installed on first switch
                                action1 = Action(act)
                                action1.setOutputAction(port12, 65535)
                                actions1.append(action1)
                                
                                match1.setInputMatch(endpoint1.interface)
                                
                                flowname1 = str(flowrule.id)
                                switch1 = endpoint1.switch_id                                
                                
                            elif endpoint1.interface == port12 and endpoint2.interface != port21:
                                #flow installed on second switch
                                action1 = Action(act)
                                action1.setOutputAction(endpoint2.interface, 65535)
                                actions1.append(action1)
                                
                                match1.setInputMatch(port21)
                                
                                flowname1 = str(flowrule.id)
                                switch1 = endpoint2.switch_id
                                
                            elif endpoint1.interface == port12 and endpoint2.interface == port21:
                                #endpoints are on the link: cannot install flow
                                logging.warning("Flow not installed for flowrule id "+flowrule.id+ ": both endpoints are on the same link")
                        else:
                            
                            if(nodes_path_flag == None):
                                self.netgraph.getTopologyGraph()
                                nodes_path = self.netgraph.getShortestPath(endpoint1.switch_id, endpoint2.switch_id)
                                nodes_path_flag = 1
                            
                            if(nodes_path == None):
                                logging.debug("[processFlowrule] Cannot find a link between " + endpoint1.switch_id + " and " + endpoint2.switch_id)
                            else:
                                logging.debug("[processFlowrule] Creating a path bewteen " + endpoint1.switch_id + " and " + endpoint2.switch_id + ". Path Length = "+str(len(nodes_path)))

            elif act.output is None:
                action = Action(act)
                actions1.append(action)
                    
        if switch1 is not None:     
            self.pushFlow(profile_graph.id, switch1, actions1, match1, flowname1, flowrule.priority, flowrule.id)
            if switch2 is not None:
                self.pushFlow(profile_graph.id, switch2, actions2, match2, flowname2, flowrule.priority, flowrule.id)
        
        # There is a path between the two endpoint
        if(nodes_path_flag is not None and nodes_path is not None):
            self.linkEndpoints(profile_graph.id, nodes_path,endpoint1,endpoint2,flowrule)            
                
                
                
                
    
    
    def pushFlow(self, session_id, switch_id, actions, match, flowname, priority, flow_id):
        flowname = flowname.replace(' ', '')
        flowtype = 'external'
        
        # ODL/Switch: Add flow rule
        flowj = Flow("flowrule", flowname, 0, priority, True, 0, 0, actions, match)
        json_req = flowj.getJSON(self.odlversion, switch_id)
        ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, switch_id, flowname)
        
        # DATABASE: Add flow rule
        flow_rule = FlowRule(_id=flowname,node_id=switch_id, _type=flowtype, status='complete',priority=priority, internal_id=flow_id)  
        GraphSession().addFlowRule(session_id, switch_id, flow_rule, None)
        
    
    
    def getLinkBetweenSwitches(self, switch1, switch2):             
        '''
        Retrieve the link between two switches, where you can find ports to use.
        switch1, switch2 = "openflow:123456789" or "00:00:64:e9:50:5a:90:90" in Hydrogen.
        '''
        
        # Get Topology
        json_data = ODL_Rest(self.odlversion).getTopology(self.odlendpoint, self.odlusername, self.odlpassword)
        topology = json.loads(json_data)
        
        if self.odlversion == "Hydrogen":
            tList = topology["edgeProperties"]
            for link in tList:
                source_node = link["edge"]["headNodeConnector"]["node"]["id"]
                dest_node = link["edge"]["tailNodeConnector"]["node"]["id"]
                if (source_node == switch1 and dest_node == switch2):
                    return link
        else:
            tList = topology["network-topology"]["topology"][0]["link"]
            for link in tList:
                source_node = link["source"]["source-node"]
                dest_node = link["destination"]["dest-node"]
                if (source_node == switch1 and dest_node == switch2):
                    return link
        return None


    
    def getLinkPortsBetweenSwitches(self, switch1, switch2):
        link = self.getLinkBetweenSwitches(switch1, switch2)
        if link is None:
            return None,None
        
        if self.odlversion == "Hydrogen":
            port12 = link["edge"]["headNodeConnector"]["id"]
            port21 = link["edge"]["tailNodeConnector"]["id"]
        else:
            tmp = link["source"]["source-tp"]
            tmpList = tmp.split(":")
            port12 = tmpList[2]

            tmp = link["destination"]["dest-tp"]
            tmpList = tmp.split(":")
            port21 = tmpList[2]
        
        # Return port12@switch1 and port21@switch2
        return port12,port21


            
    



    def linkEndpoints(self,session_id, path,ep1,ep2,flowrule):

        flow_id = flowrule.id
        flow_priority = flowrule.priority
        actions = []
        vlan_id = None
        
        print ""
        print "Flow id: "+str(flow_id)
        print "Flow priority: "+str(flow_priority)        
        
        
        # Clean actions
        for a in flowrule.actions:
            
            # Store the VLAN ID and remove the action
            if a.set_vlan_id is not None:
                vlan_id = a.set_vlan_id
                continue
            
            # Filter non OUTPUT actions 
            if a.output is None:
                action = Action(a)
                actions.append(action)
                
        
        #TODO: Keep track of all vlan ID
        if vlan_id is not None:
            '''
                - controlla se l'id e' gia' usato nella rete
                - eventualmente ne recupera un'altro
                - vlan_id = <nuovo vlan id>
                
                quando viene richiesto di collegare due endpoint lontani
                la prima soluzione e' lavorare con le vlan; ma l'id della vlan
                sarebbe meglio che non venisse specificato nel grafo, ma che 
                fosse deciso automaticamente comunicandolo infine a chi ha fatto
                la richiesta originale del collegamento dei due endpoint.
                
            '''
            print ""
        
        
        # Traverse the path and create the flow for each switch
        for i in range(0, len(path)):
            hop = path[i]
            
            match = Match(flowrule.match)
            new_actions = list(actions)
            
            if i==0:
                #first switch
                switch_id = ep1.switch_id
                port_in = ep1.interface
                port_out = self.netgraph.topology[hop][path[i+1]]['from_port']
                
                if vlan_id is not None:
                    action_pushvlan = Action()
                    action_pushvlan.setPushVlanAction()
                    new_actions.append(action_pushvlan)
                    
                    action_setvlan = Action()
                    action_setvlan.setSwapVlanAction(vlan_id)
                    new_actions.append(action_setvlan)
                
            elif i==len(path)-1:
                #last switch
                switch_id = ep2.switch_id
                port_in = self.netgraph.topology[path[i-1]][hop]['to_port']
                port_out = ep2.interface
                
                if vlan_id is not None:
                    match.setVlanMatch(vlan_id)
                    action_stripvlan = Action()
                    action_stripvlan.setPopVlanAction()
                    new_actions.append(action_stripvlan)

            else:
                #middle way switch
                switch_id = hop
                port_in = self.netgraph.topology[path[i-1]][hop]['to_port']
                port_out = self.netgraph.topology[hop][path[i+1]]['from_port']
                
                if vlan_id is not None:
                    match.setVlanMatch(vlan_id)
                
            print switch_id+" from "+str(port_in)+" to "+str(port_out)
            
            match.setInputMatch(port_in)
            
            action_output = Action()
            action_output.setOutputAction(port_out, 65535)
            new_actions.append(action_output)
            
            flow_name = str(flow_id)+"_"+str(i)
            
            self.pushFlow(session_id, switch_id, new_actions, match, flow_name, flow_priority, flow_id)
        
        return

    
        
        
        
    