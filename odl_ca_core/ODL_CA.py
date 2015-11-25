'''
Created on 13/apr/2015
@author: vida
'''

import logging, json
from __builtin__ import str

from nffg_library.nffg import FlowRule

from odl_ca_core.config import Configuration
from odl_ca_core.exception import GraphError

from odl_ca_core.sql.graph import Graph
from odl_ca_core.sql.node import Node

from odl_ca_core.ODL_Rest import ODL_Rest
from odl_ca_core.resources import Action, Match, Flow, ProfileGraph, Endpoint
from odl_ca_core.netgraph import NetGraph

DEBUG_MODE = Configuration().DEBUG_MODE
JOLNET_NETWORKS = Configuration().JOLNET_NETWORKS

class OpenDayLight_CA():
    
    def __init__(self, graph_id, userdata):

        self.graph_id = graph_id
        
        #credentials to get Keystone token for the user
        self.userdata = userdata
    
    
    
    '''
    ######################################################################################################
    ##############################    Component Adapter Interface        #################################
    ######################################################################################################
    '''
    
    @property
    def URI(self):
        return self.compute_node_address
    
    
    
    def instantiateProfile(self, nf_fg, node):
        '''
        Instantiate the User Profile Graph
        Args:
            nffg:
                Object of the Class Common.NF_FG.nf_fg.NF_FG
            node:
                Object of the class Common.SQL.node.NodeModel
            Exceptions:
                Raise some exception to be captured
        '''
        self.getAuthTokenAndEndpoints(node)
        
        logging.debug("Forwarding graph: " + nf_fg.getJSON(True))
        try:            
            #Read the nf_fg JSON structure and map it into the proper objects and db entries
            profile_graph = self.buildProfileGraph(nf_fg)
            self.openstackResourcesInstantiation(profile_graph, nf_fg)
            logging.debug("Graph " + profile_graph.id + " correctly instantiated!")
            
        except Exception as err:
            logging.error(err.message)
            logging.exception(err) 
            raise err
    
    
    
    def updateProfile(self, new_nf_fg, old_nf_fg, node):
        '''
        Update a User Profile Graph
        Args:
            new_nffg:
                Object of the Class Common.NF_FG.nf_fg.NF_FG
            old_nffg:
                Object of the Class Common.NF_FG.nf_fg.NF_FG
            node:
                Object of the class Common.SQL.node.NodeModel
            Exceptions:
                Raise some exception to be captured
        '''       
        self.getAuthTokenAndEndpoints(node)
        
        try:
            updated_nffg = old_nf_fg.diff(new_nf_fg)
            logging.debug("Diff: "+updated_nffg.getJSON(True))            
                
            #self.openstackResourcesControlledDeletion(updated_nffg, self.token.get_token())
            self.openstackResourcesControlledDeletion(updated_nffg, None)
            Graph().updateNFFG(updated_nffg, self.graph_id)
            profile_graph = self.buildProfileGraph(updated_nffg)
            self.openstackResourcesInstantiation(profile_graph, updated_nffg)
            logging.debug("Graph " + old_nf_fg.id + " correctly updated!")
            
        except Exception as err:
            logging.error(err.message)
            logging.exception(err) 
            raise err
    
    
    
    def deinstantiateProfile(self, nf_fg, node):
        '''
        De-instantiate the User Profile Graph
        Args:
            nffg:
                Object of the Class Common.NF_FG.nf_fg.NF_FG
            node_endpoint:
                Object of the class Common.SQL.node.NodeModel
            Exceptions:
                Raise some exception to be captured
        '''
        self.getAuthTokenAndEndpoints(node)
        
        logging.debug("Forwarding graph: " + nf_fg.getJSON())
        
        try:
            self.openstackResourcesDeletion()
            logging.debug("Graph " + nf_fg.id + " correctly deleted!") 
        except Exception as err:
            logging.error(err.message)
            logging.exception(err) 
            raise err
 
 
 
 
 
    '''
    ######################################################################################################
    ######################   Authentication towards infrastructure controllers        ####################
    ######################################################################################################
    ''' 
    def getAuthTokenAndEndpoints(self, node):

        # Dati ODL
        odl = Node().getOpenflowController(node.openflow_controller)
        self.odlendpoint = odl.endpoint
        self.odlusername = odl.username
        self.odlpassword = odl.password
        self.odlversion = odl.version
        self.netgraph = NetGraph(self.odlversion, self.odlendpoint, self.odlusername, self.odlpassword)
    
    
    
    
    
    
    
    
    
    '''
    ######################################################################################################
    #############################    Resources preparation phase        ##################################
    ######################################################################################################
    '''      
    def buildProfileGraph(self, nf_fg):
        profile_graph = ProfileGraph()
        profile_graph.setId(nf_fg.id)
        
        #Remove from the pool of available openstack networks vlans used in endpoints of type vlan
        for endpoint in nf_fg.end_points:
            if endpoint.type == 'vlan':
                if endpoint.vlan_id.isdigit() is False:
                    name = endpoint.vlan_id
                else:                                
                    name = "exp" + str(endpoint.vlan_id)                
                JOLNET_NETWORKS.remove(name)
        
        '''
        for vnf in nf_fg.vnfs:
            nf = self.buildVNF(vnf)
            profile_graph.addVNF(nf)
        
        for vnf in profile_graph.functions.values():
            #nf = profile_graph.functions[vnf.id]
            self.setVNFNetwork(nf_fg, vnf, profile_graph)
            #self.setVNFNetwork(nf_fg, vnf, nf)
        '''

        for endpoint in nf_fg.end_points:
            ep = self.buildEndpoint(endpoint)
            profile_graph.addEndpoint(ep)
        
        for flowrule in nf_fg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            profile_graph.addFlowrule(flowrule)
                  
        return profile_graph                        
    
              
                
    def buildEndpoint(self, endpoint):
        if endpoint.status is None:
            status = "new"
        else:
            status = endpoint.status
        
        '''
        if endpoint.remote_endpoint_id is not None:
            delimiter = endpoint.remote_endpoint_id.find(":")
            remote_graph = endpoint.remote_endpoint_id[:delimiter]
            remote_id = endpoint.remote_endpoint_id[delimiter+1:] 
            return Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.switch_id, endpoint.interface, status, remote_graph, remote_id)
        else:
        '''
        return Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.switch_id, endpoint.interface, status)
    
    
    
    
    '''
    ######################################################################################################
    ##########################    Resources instantiation and deletion        ############################
    ######################################################################################################
    ''' 
    def openstackResourcesInstantiation(self, profile_graph, nf_fg):        
                   
        #Create flow on the SDN network for graphs interconnection
        for endpoint in profile_graph.endpoints.values():
            if endpoint.status == "new":
                
                '''
                if endpoint.remote_id is not None:
                    #Check if the remote graph exists and the requested endpoint is available
                    graph = Graph().get_nffg(endpoint.remote_graph)
                    remote_endpoint = None
                    remote_endpoint = graph.getEndPoint(endpoint.remote_id)
                    
                    if remote_endpoint is not None:
                        vlan = remote_endpoint.vlan_id
                        switch1 = endpoint.switch_id
                        port1 = endpoint.interface                                       
                                                                  
                        switch1_id = Node().getNodeFromDomainID(switch1).id
                        switch2_id = Graph().getNodeID(endpoint.remote_graph)
                        switch2 = Node().getNodeDomainID(switch2_id)     
                        port2 = remote_endpoint.interface
                        
                        #TODO: add the port on the endpoint switch
                        self.linkZones(self.graph_id, switch1, port1, switch1_id, switch2, port2, switch2_id, vlan, nf_fg.getEndPoint(endpoint.id).db_id)
                    else:
                        logging.error("Remote graph " + endpoint.remote_graph + " has not a " + endpoint.id + " endpoint available!")
                '''
                
                Graph().setEndpointLocation(self.graph_id, endpoint.id, endpoint.interface)
          
        
        for flowrule in profile_graph.flowrules.values():
            if flowrule.status =='new':
                #TODO: check priority
                if flowrule.match is not None:
                    if flowrule.match.port_in is not None:
                        tmp1 = flowrule.match.port_in.split(':')
                        port1_type = tmp1[0]
                        port1_id = tmp1[1]
                        
                        '''
                        if port1_type == 'vnf':
                            if len(flowrule.actions) > 1 or flowrule.actions[0].output is None:
                                raise GraphError("Multiple actions or action different from output are not supported between vnfs")
                        elif port1_type == 'endpoint':
                        '''
                        
                        if port1_type == 'endpoint':
                            '''
                            endpoint_to_vnf = False
                            for action in flowrule.actions:
                                if action.output is not None and action.output.split(':')[0] == "vnf":
                                    endpoint_to_vnf= True
                                    break
                            if endpoint_to_vnf is True:
                                if len(flowrule.actions) > 1:
                                    raise GraphError("Multiple actions are not supported between an endpoint and a vnf")
                                else:
                                    continue
                            '''
                            endp1 = profile_graph.endpoints[port1_id]
                            if endp1.type == 'interface':        
                                self.processFlowrule(endp1, flowrule, profile_graph)  
          
                                  
            
    def openstackResourcesDeletion(self):       
        #Delete every resource one by one
        flows = Graph().getFlowRules(self.graph_id)
        for flow in flows:
            if flow.type == "external" and flow.status == "complete":
                switch_id = Node().getNodeDomainID(flow.node_id)
                ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, switch_id, flow.graph_flow_rule_id)
                
        #TODO: Delete also networks and subnets if previously created
        
        
        
    def openstackResourcesControlledDeletion(self, updated_nffg, token_id):

        for endpoint in updated_nffg.end_points[:]:
            if endpoint.status == 'to_be_deleted':                      
                flows = Graph().getEndpointResource(endpoint.db_id, "flowrule")
                for flow in flows:
                    if flow.type == "external" and flow.status == "complete":
                        switch_id = Node().getNodeDomainID(flow.node_id)
                        ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, switch_id, flow.id)
                        #Graph().deleteFlowRule(flow.db_id)
                Graph().deleteEndpoint(endpoint.id, self.graph_id)
                Graph().deleteEndpointResourceAndResources(endpoint.db_id)
                if endpoint.remote_endpoint_id is not None:
                    Graph().deleteGraphConnection(endpoint.db_id) 
                updated_nffg.end_points.remove(endpoint)  
                      
        for flowrule in updated_nffg.flow_rules[:]:
            if flowrule.status == 'to_be_deleted' and flowrule.type != 'external':
                self.deleteFlowRule(flowrule, updated_nffg)

     
     
     
     
     
    '''
    ######################################################################################################
    #########################    Interactions with OpenDaylight              #############################
    ######################################################################################################
    ''' 
    
    def getLinkBetweenSwitches(self, switch1, switch2):             
        '''
        Retrieve the link between two switches, where you can find ports to use
        Args:
            switch1:
                OpenDaylight identifier of the source switch (example: openflow:123456789 or 00:00:64:e9:50:5a:90:90 in Hydrogen)
            switch2:
                OpenDaylight identifier of the destination switch (example: openflow:987654321 or 00:00:64:e9:50:5a:90:90 in Hydrogen)
        '''
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
    
    
    
    
    
    def pushVlanFlow(self, source_node, flow_id, vlan, in_port, out_port):
        '''
        Push a flow into a Jolnet switch with 
            matching on VLAN id and input port
            output through the specified port
        Args:
            source_node:
                OpenDaylight identifier of the source switch (example: openflow:123456789 or 00:00:64:e9:50:5a:90:90 in Hydrogen)
            flow_id:
                unique identifier of the flow on the whole OpenDaylight domain
            vlan:
                VLAN id of the traffic (for matching)
            in_port:
                ingoing port of the traffic (for matching)
            out_port:
                output port where to send out the traffic (action)
        '''
        action1 = Action()
        action1.setOutputAction(out_port, 65535)
        actions = [action1]
        
        match = Match()
        match.setInputMatch(in_port)
        match.setVlanMatch(vlan)
        
        flowj = Flow("jolnetflow", flow_id, 0, 65535, True, 0, 0, actions, match)        
        json_req = flowj.getJSON(self.odlversion, source_node)
        ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, source_node, flow_id)





    def linkZones(self, graph_id, switch_user, port_vms_user, switch_user_id, switch_isp, port_vms_isp, switch_isp_id, vlan_id, endpoint_db_id):
        '''
        Link two graphs (or two parts of a single graph) through the SDN network
        Args:
            graph_id:
                id of the user's graph
            switch_user:
                OpenDaylight identifier of the first switch (example: openflow:123456789 or 00:00:64:e9:50:5a:90:90 in Hydrogen)
            port_vms_user:
                port on the OpenFlow switch where virtual machines are linked
            switch_user_id:
                id of the node in the database
            switch_isp:
                OpenDaylight identifier of the second switch (example: openflow:987654321 or 00:00:64:e9:50:5a:90:90 in Hydrogen)
            port_vms_isp:
                port on the OpenFlow switch where virtual machines are linked
            switch_isp_id:
                id of the node in the database
            vlan_id:
                VLAN id of the OpenStack network which links the graphs
        '''
        edge = None
        link = None
        if self.odlversion == "Hydrogen":
            edge = self.getLinkBetweenSwitches(switch_user, switch_isp)
            if edge is not None:
                port12 = edge["edge"]["headNodeConnector"]["id"]
                port21 = edge["edge"]["tailNodeConnector"]["id"]    
        else:
            link = self.getLinkBetweenSwitches(switch_user, switch_isp)
            if link is not None:        
                tmp = link["source"]["source-tp"]
                tmpList = tmp.split(":")
                port12 = tmpList[2]
                    
                tmp = link["destination"]["dest-tp"]
                tmpList = tmp.split(":")
                port21 = tmpList[2]
                
        if link is not None or edge is not None:
            fid = int(str(vlan_id) + str(1))              
            self.pushVlanFlow(switch_user, fid, vlan_id, port_vms_user, port12)
            flow_rule = FlowRule(_id=fid,node_id=Node().getNodeFromDomainID(switch_user).id,_type='external', status='complete',priority=65535)  
            #Graph().addFlowRule(self.graph_id, flow_rule, None)
            Graph().addFlowRuleAsEndpointResource(self.graph_id, flow_rule, None, endpoint_db_id)
            
            fid = int(str(vlan_id) + str(2))
            self.pushVlanFlow(switch_isp, fid, vlan_id, port21, port_vms_isp)
            flow_rule = FlowRule(_id=fid,node_id=Node().getNodeFromDomainID(switch_isp).id,_type='external', status='complete',priority=65535)  
            #Graph().addFlowRule(self.graph_id, flow_rule, None)
            Graph().addFlowRuleAsEndpointResource(self.graph_id, flow_rule, None, endpoint_db_id)
            
            fid = int(str(vlan_id) + str(3))               
            self.pushVlanFlow(switch_isp, fid, vlan_id, port_vms_isp, port21)
            flow_rule = FlowRule(_id=fid,node_id=Node().getNodeFromDomainID(switch_isp).id,_type='external', status='complete',priority=65535)  
            #Graph().addFlowRule(self.graph_id, flow_rule, None)
            Graph().addFlowRuleAsEndpointResource(self.graph_id, flow_rule, None, endpoint_db_id)

            fid = int(str(vlan_id) + str(4))               
            self.pushVlanFlow(switch_user, fid, vlan_id, port12, port_vms_user)
            flow_rule = FlowRule(_id=fid,node_id=Node().getNodeFromDomainID(switch_user).id,_type='external', status='complete',priority=65535)  
            #Graph().addFlowRule(self.graph_id, flow_rule, None)
            Graph().addFlowRuleAsEndpointResource(self.graph_id, flow_rule, None, endpoint_db_id)
        else:
            logging.debug("[linkZones] Cannot find a link between " + switch_user + " and " + switch_isp)
            
    
    
    
            
    def processFlowrule(self, endpoint1, flowrule, profile_graph):
        #flowrule = copy.deepcopy(flowrule_original)
        match1 = Match(flowrule.match)
        match2 = None
        actions1 = []
        actions2 = []
        switch1 = None
        switch2 = None
        flowname1 = None
        flowname2 = None        
        #second_flow = False
        
        nodes_path = None
        nodes_path_flag = None
        print "\n\n\nprocessFlowrule"
        
        for act in flowrule.actions:
            if act.drop is True:
                action = Action(act)
                actions = [action]
                match1.setInputMatch(endpoint1.interface)
                flowname = str(flowrule.id)
                flowj = Flow("flowrule", flowname, 0, flowrule.priority, True, 0, 0, actions, match1)        
                json_req = flowj.getJSON(self.odlversion, endpoint1.switch_id)
                ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, endpoint1.switch_id, flowname)
                
                flow_rule = FlowRule(_id=flowname,node_id=Node().getNodeFromDomainID(endpoint1.switch_id).id,_type='external', status='complete',priority=flowrule.priority, internal_id=flowrule.id)  
                Graph().addFlowRule(self.graph_id, flow_rule, None)
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
                        edge = None
                        link = None
                        if self.odlversion == "Hydrogen":
                            edge = self.getLinkBetweenSwitches(endpoint1.switch_id, endpoint2.switch_id)
                            if edge is not None:
                                port12 = edge["edge"]["headNodeConnector"]["id"]
                                port21 = edge["edge"]["tailNodeConnector"]["id"]        
                        else:
                            link = self.getLinkBetweenSwitches(endpoint1.switch_id, endpoint2.switch_id)
                            if link is not None:            
                                tmp = link["source"]["source-tp"]
                                tmpList = tmp.split(":")
                                port12 = tmpList[2]
                                        
                                tmp = link["destination"]["dest-tp"]
                                tmpList = tmp.split(":")
                                port21 = tmpList[2]
                                
                        if link is not None or edge is not None:
                            if endpoint1.interface != port12 and endpoint2.interface != port21:
                                # endpoints are not on the link: 2 flows 
                                action1 = Action(act)
                                
                                #print vars(action1)
                                
                                #self.netgraph.print_json(json.load(action1))
                                action1.setOutputAction(port12, 65535)
                                actions1.append(action1)
                                
                                #print vars(action1)
                                
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
            self.pushFlow(switch1, actions1, match1, flowname1, flowrule.priority, flowrule.id)
            if switch2 is not None:
                self.pushFlow(switch2, actions2, match2, flowname2, flowrule.priority, flowrule.id)
        
        # There is a path between the two endpoint
        if(nodes_path_flag is not None and nodes_path is not None):
            self.linkEndpoints(nodes_path,endpoint1,endpoint2,flowrule)





    def linkEndpoints(self,path,ep1,ep2,flowrule):

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
            
            self.pushFlow(switch_id, new_actions, match, flow_name, flow_priority, flow_id)
        
        return



    

    def pushFlow(self, switch_id, actions, match, flowname, priority, flow_id):
        flowname = flowname.replace(' ', '')
        flowj = Flow("flowrule", flowname, 0, priority, True, 0, 0, actions, match)
        
        json_req = flowj.getJSON(self.odlversion, switch_id)
        
        print json_req
        
        #return
        
        ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, switch_id, flowname)
        
        flow_rule = FlowRule(_id=flowname,node_id=Node().getNodeFromDomainID(switch_id).id,_type='external', status='complete',priority=priority, internal_id=flow_id)  
        Graph().addFlowRule(self.graph_id, flow_rule, None)
    



    
    def deleteFlowRule(self, flowrule, nf_fg):    
        #flowname = flowrule.id.replace(' ' ,'')
        flows = Graph().getFlowRules(self.graph_id)
        for flow in flows:
            if flow.type == "external" and flow.status == "complete" and flow.internal_id == flowrule.id:
                switch_id = Node().getNodeDomainID(flow.node_id)
                ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, switch_id, flow.graph_flow_rule_id)
                Graph().deleteFlowRule(flow.id)
        Graph().deleteFlowRule(flowrule.db_id)
        nf_fg.flow_rules.remove(flowrule)
            
