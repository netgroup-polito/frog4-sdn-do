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
from odl_ca_core.odl_rest import ODL_Rest
from odl_ca_core.resources import Action, Match, Flow, ProfileGraph, Endpoint
from odl_ca_core.netgraph import NetGraph
from odl_ca_core.exception import sessionNotFound, GraphError, NffgUselessInformations






class OpenDayLightCA(object):

    def __init__(self, user_data):
        
        conf = Configuration()
        
        self._session_id = None
        
        self.nffg = None
        self.user_data = user_data
        '''
        Fields:
         - user_data.username
         - user_data.password
         - user_data.tenant
        '''
        
        # Dati ODL
        self.odlendpoint = conf.ODL_ENDPOINT
        self.odlversion = conf.ODL_VERSION
        self.odlusername = conf.ODL_USERNAME
        self.odlpassword = conf.ODL_PASSWORD
        
        # NetGraph
        self.netgraph = NetGraph(self.odlversion, self.odlendpoint, self.odlusername, self.odlpassword)



    def NFFG_Put(self, nffg):
        '''
        Manage the request of NF-FG instantiation
        '''
        logging.debug("Put NF-FG: put from user "+self.user_data.username+" on tenant "+self.user_data.tenant)
        
        # Check if the NF-FG is already instantiated, update it and exit
        if self.NFFG_Update(nffg) is not None:
            return self._session_id
            
        # Instantiate a new NF-FG
        try:
            self._session_id = GraphSession().addNFFG(nffg, self.user_data.getUserID())
            logging.debug("Put NF-FG: instantiating a new nffg: " + nffg.getJSON(True))
            
            # Profile graph for ODL functions
            profile_graph = self.__ProfileGraph_BuildFromNFFG(nffg)
            
            # Write latest info in the database and send all the flow rules to ODL
            self.__ODL_FlowsInstantiation(profile_graph)
            
            logging.debug("Put NF-FG: session " + self._session_id + " correctly instantiated!")

        except Exception as ex:
            logging.error(ex.message)
            logging.exception(ex.message)
            GraphSession().deleteGraph(self._session_id)
            GraphSession().setErrorStatus(self._session_id)
            raise ex
        
        GraphSession().updateStatus(self._session_id, 'complete')                                
        return self._session_id

    
    
    def NFFG_Update(self, new_nffg):

        # Check and get the session id for this user-graph couple
        logging.debug("Update NF-FG: check if the user "+self.user_data.getUserID()+" has already instantiated the graph "+new_nffg.id+".")
        session = GraphSession().getActiveSession(self.user_data.getUserID(), new_nffg.id, error_aware=True)
        if session is None:
            return None
        self._session_id = session.session_id
        
        logging.debug("Update NF-FG: already instantiated, trying to update it")
        logging.debug("Update NF-FG: updating session "+self._session_id+" from user "+self.user_data.username+" on tenant "+self.user_data.tenant)
        GraphSession().updateStatus(self._session_id, 'updating')

        # Get the old NFFG
        old_nffg = GraphSession().getNFFG(self._session_id)
        logging.debug("Update NF-FG: the old session: "+old_nffg.getJSON())
        
        # TODO: remove or integrate remote_graph and remote_endpoint

        try:
            updated_nffg = old_nffg.diff(new_nffg)
            logging.debug("Update NF-FG: coming updates: "+updated_nffg.getJSON(True))            
            
            # Delete useless endpoints and flowrules 
            self.__ODL_FlowsControlledDeletion(updated_nffg)
            
            # Update database and send flowrules to ODL
            GraphSession().updateNFFG(updated_nffg, self._session_id)
            profile_graph = self.__ProfileGraph_BuildFromNFFG(updated_nffg)
            self.__ODL_FlowsInstantiation(profile_graph)
            
            logging.debug("Update NF-FG: session " + self._session_id + " correctly updated!")
            
        except Exception as ex:
            logging.error("Update NF-FG: "+ex.message)
            logging.exception("Update NF-FG: "+ex.message)
            # TODO: discuss... delete the graph when an error occurs in this phase?
            #GraphSession().deleteGraph(self._session_id)
            #GraphSession().setErrorStatus(self._session_id)
            raise ex
        
        GraphSession().updateStatus(self._session_id, 'complete')
        return self._session_id
    
    
    
    def NFFG_Delete(self, nffg_id):
        
        session = GraphSession().getActiveSession(self.user_data.getUserID(), nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Delete NF-FG: session not found for graph "+str(nffg_id))
        
        self._session_id = session.session_id
        
        logging.debug("Delete NF-FG: deleting session "+str(self._session_id))

        instantiated_nffg = GraphSession().getNFFG(self._session_id)
        logging.debug("Delete NF-FG: we are going to delete: "+instantiated_nffg.getJSON())
    
        try:
            self.__ODL_FlowsDeletion(self._session_id)
            logging.debug("Delete NF-FG: session " + self._session_id + " correctly deleted!")
            
        except Exception as ex:
            logging.error("Delete NF-FG: "+ex.message)
            logging.exception("Delete NF-FG: "+ex.message)
            #raise ex - no raise because we need to delete the session in any case
        GraphSession().deleteGraph(self._session_id)
        GraphSession().setEnded(self._session_id)



    def NFFG_Get(self, nffg_id):
        session = GraphSession().getActiveSession(self.user_data.getUserID(), nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Get NF-FG: session not found, for graph "+str(nffg_id))
        
        self._session_id = session.session_id
        logging.debug("Getting session: "+str(self._session_id))
        return GraphSession().getNFFG(self._session_id).getJSON()



    def NFFG_Status(self, nffg_id):
        session = GraphSession().getActiveSession(self.user_data.getUserID(),nffg_id,error_aware=True)
        if session is None:
            raise sessionNotFound("Status NF-FG: session not found, for graph "+str(nffg_id))
        
        self._session_id = session.session_id
        logging.debug("Status NF-FG: graph status: "+str(session.status))
        return session.status
    
    
    
    def NFFG_Validate(self, nffg):
        '''
        A validator for this specific control adapter.
        The original json, as specified in the extern NFFG library,
        could contain useless objects and fields for this CA.
        If this happens, we have to raise exceptions to stop the request processing.  
        '''        
        if len(nffg.vnfs)>0:
            msg = "NFFG: presence of 'VNFs'. This CA does not process this information."
            logging.debug(msg)
            raise NffgUselessInformations(msg)
        
        for ep in nffg.end_points:
            if(ep.remote_endpoint_id is not None):
                msg = "NFFG: presence of 'end-points.remote_endpoint_id'. This CA does not process this information."
                logging.debug(msg)
                raise NffgUselessInformations(msg)
            if(ep.remote_ip is not None):
                msg = "NFFG: presence of 'end-points.remote-ip'. This CA does not process this information."
                logging.debug(msg)
                raise NffgUselessInformations(msg)
            if(ep.type <> "interface"):
                msg = "NFFG: 'end-points.type' must be 'interface'."
                logging.debug(msg)
                raise NffgUselessInformations(msg)



    def __ProfileGraph_BuildFromNFFG(self, nffg):
        '''
        Create a ProfileGraph with the flowrules and endpoints specified in nffg.
        Args:
            nffg:
                Object of the Class Common.NF_FG.nffg.NF_FG
        Return:
            Object of the Class odl_ca_core.resources.ProfileGraph
        '''
        profile_graph = ProfileGraph()

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




     
    '''
    ######################################################################################################
    #########################    Interactions with OpenDaylight              #############################
    ######################################################################################################
    '''
        
    def __ODL_FlowsInstantiation(self, profile_graph):
        
        # Create the endpoints
        # for endpoint in profile_graph.endpoints.values():
        #    if endpoint.status == "new":
                # TODO: remove or integrate remote_graph and remote_endpoint

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
                                self.__ODL_ProcessFlowrule(endp1, flowrule, profile_graph)



    def __ODL_FlowsDeletion(self, session_id):       
        #Delete every flow from ODL
        flows = GraphSession().getFlowrules(session_id)
        for flow in flows:
            if flow.type == "external" and flow.status == "complete":
                ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow.switch_id, flow.internal_id)



    def __ODL_FlowsControlledDeletion(self, updated_nffg):
        
        # Delete the endpoints 'to_be_deleted'
        for endpoint in updated_nffg.end_points[:]:
            if endpoint.status == 'to_be_deleted':
                
                # TODO: remove or integrate remote_graph, remote_endpoint, endpoint_resource "flowrule", and graph_connection
                
                # Delete endpoints and all resourcess associated to it.
                GraphSession().deleteEndpoint(endpoint.id, self._session_id)
                GraphSession().deleteEndpointResourceAndResources(endpoint.db_id)
                
                updated_nffg.end_points.remove(endpoint)  
        
        # Delete the flowrules 'to_be_deleted'              
        for flowrule in updated_nffg.flow_rules[:]:
            if flowrule.status == 'to_be_deleted' and flowrule.type != 'external':
                
                # Get and delete the flow rules with the same flow.internal_id,
                # which are the flow rules effectively pushed in ODL.
                # TODO: improve query
                flows = GraphSession().getFlowrules(self._session_id)
                for flow in flows:
                    if flow.type == "external" and flow.status == "complete" and flow.graph_flow_rule_id == flowrule.id:
                        ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow.switch_id, flow.internal_id)
                        GraphSession().deleteFlowrule(flow.id)
                
                # Finally, delete the main flow rule (that written in nffg.json)
                GraphSession().deleteFlowrule(flowrule.db_id)
                updated_nffg.flow_rules.remove(flowrule)
    




    class __processedFLowrule(object):
            
        def __init__(self,switch_id=None,match=None,actions=None,flow_id=None,priority=None,flowname_suffix=None):
            self.__switch_id = switch_id
            self.__match = match
            self.set_actions(actions)
            self.set_flow_id(flow_id)
            self.set_flow_name(flowname_suffix)
            self.__priority = priority
            self.__vlan_id = None
            

        def get_switch_id(self):
            return self.__switch_id

        def get_match(self):
            return self.__match

        def get_actions(self):
            return self.__actions

        def get_flow_id(self):
            return self.__flow_id

        def get_flow_name(self):
            return self.__flow_name

        def get_priority(self):
            return self.__priority
        
        def get_vlan_id(self):
            return self.__vlan_id


        def set_switch_id(self, value):
            self.__switch_id = value

        def set_match(self, value):
            self.__match = value

        def set_actions(self, value):
            if value is None:
                self.__actions = []
            else:
                self.__actions = value
        
        def append_action(self, value):
            if value is None:
                return
            self.__actions.append(value)
            
        def __reset_flow_name(self):
            self.__flow_name = str(self.__flow_id)+"_"
            
        def set_flow_id(self, value):
            self.__flow_id = value
            self.__reset_flow_name()

        def set_flow_name(self, suffix):
            self.__reset_flow_name()
            if(suffix is not None):
                self.__flow_name = self.__flow_name + str(suffix)

        def set_priority(self, value):
            self.__priority = value
        
        def set_vlan_id(self, value):
            self.__vlan_id = value
            
            


        def setFr1(self, switch_id, action, port_in, port_out, flowname_suffix):
            if(self.__match is None):
                self.__match = Match()
            new_act = Action(action)
            if(port_out is not None):
                new_act.setOutputAction(port_out, 65535)
            
            self.__actions.append(new_act)
            self.__match.setInputMatch(port_in)
            self.__switch_id = switch_id
            self.__flow_name = self.__flow_name+flowname_suffix

        
        def isReady(self):
            return ( self.__switch_id is not None and self.__flow_id is not None )






    def __ODL_ProcessFlowrule(self, endpoint1, flowrule, profile_graph):
        #Process a flow rule written in the section "big switch" of a nffg json.
        
        fr1 = OpenDayLightCA.__processedFLowrule(match=Match(flowrule.match),
                                                  priority=flowrule.priority,
                                                  flow_id=flowrule.id)
        
        fr2 = OpenDayLightCA.__processedFLowrule(priority=flowrule.priority,
                                                  flow_id=flowrule.id)

           
        nodes_path = None
        nodes_path_flag = None
        
        print "\n\n\nodlProcessFlowrule"
        
        # Add "Drop" flow rules only, and return.
        # If a flow rule has a drop action, we don't care other actions!
        for a in flowrule.actions:
            if a.drop is True:
                fr1.setFr1(endpoint1.switch_id, a, endpoint1.interface , None, "1")
                self.__ODL_PushFlow(fr1)
                return  
        
        # Split the action handling in output and non-output.
        for a in flowrule.actions:
            
            # If this action is not an output action,
            # we just append it to the final actions list 'actions1'.
            if a.output is None:
                no_output = Action(a)
                fr1.append_action(no_output)
            
            # If this action is an output action (a.output is not None),
            # we check that the output is an endpoint and manage the main cases.
            else:
                
                # Is the 'output' destination an endpoint?
                tmp2 = a.output.split(':')
                port2_type = tmp2[0]
                port2_id = tmp2[1]
                if port2_type == 'endpoint':
                    endpoint2 = profile_graph.endpoints[port2_id]
                    
                    # Endpoints are on the same switch
                    if endpoint1.switch_id == endpoint2.switch_id:
                        
                        # Error: endpoints are equal!
                        if endpoint1.interface == endpoint2.interface:
                            raise GraphError("Flowrule "+flowrule.id+" is wrong: endpoints are overlapping")
                        
                        # Install a flow between two ports of the switch
                        else:
                            fr1.setFr1(endpoint1.switch_id, a, endpoint1.interface , endpoint2.interface, "1")
                    
                    # Endpoints are on different switches              
                    else:
                        
                        # Check if a link between endpoint switches exists.
                        # Return: port12 (on endpoint1 switch) and port21 (on endpoint2 switch).
                        port12,port21 = self.__ODL_GetLinkPortsBetweenSwitches(endpoint1.switch_id, endpoint2.switch_id)       
                        
                        # A link between endpoint switches exists!
                        if port12 is not None and port21 is not None:
                            
                            # Endpoints are not on the link: 2 flows (most probable setup) 
                            if endpoint1.interface != port12 and endpoint2.interface != port21:
                                fr1.setFr1(endpoint1.switch_id, a, endpoint1.interface , port12, "1")
                                fr2.setFr1(endpoint2.switch_id, None, port21 , endpoint2.interface, "2")
                            
                            # Flow installed on first switch
                            elif endpoint1.interface != port12 and endpoint2.interface == port21:
                                fr1.setFr1(endpoint1.switch_id, a, endpoint1.interface , port12, "1")
                                                                
                            # Flow installed on second switch                                
                            elif endpoint1.interface == port12 and endpoint2.interface != port21:
                                fr1.setFr1(endpoint2.switch_id, a, endpoint2.interface , port21, "2")
                            
                            # Endpoints are on the link: cannot install flow
                            elif endpoint1.interface == port12 and endpoint2.interface == port21:
                                logging.warning("Flow not installed for flowrule id "+flowrule.id+ ": both endpoints are on the same link")
                        
                        # No link between endpoint switches...search for a path!
                        else:
                            if(nodes_path_flag == None):
                                self.netgraph.getTopologyGraph()
                                nodes_path = self.netgraph.getShortestPath(endpoint1.switch_id, endpoint2.switch_id)
                                nodes_path_flag = 1
                            
                            if(nodes_path == None):
                                logging.debug("Cannot find a link between "+endpoint1.switch_id+" and "+endpoint2.switch_id)
                            else:
                                logging.debug("Creating a path bewteen "+endpoint1.switch_id+" and "+endpoint2.switch_id+". "+
                                              "Path Length = "+str(len(nodes_path)))
        # Push the fr1, if it is ready                
        if fr1.isReady():
            self.__ODL_PushFlow(fr1)
        
            # Push the fr2, if it is ready     
            if fr2.isReady():
                self.__ODL_PushFlow(fr2)
        
        # There is a path between the two endpoint
        if(nodes_path_flag is not None and nodes_path is not None):
            self.__ODL_LinkEndpoints(nodes_path, endpoint1, endpoint2, flowrule)





    def __ODL_PushFlow(self, pfr):
        # pfr = __processedFLowrule

        # ODL/Switch: Add flow rule
        flowj = Flow("flowrule", pfr.get_flow_name(), 0, pfr.get_priority(), True, 0, 0, pfr.get_actions(), pfr.get_match())
        json_req = flowj.getJSON(self.odlversion, pfr.get_switch_id())
        ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, pfr.get_switch_id(), pfr.get_flow_name())
        
        # DATABASE: Add flow rule and vlan tracking
        flow_rule = FlowRule(_id=pfr.get_flow_id(),node_id=pfr.get_switch_id(), _type='external', status='complete',priority=pfr.get_priority(), internal_id=pfr.get_flow_name())  
        flow_rule_db_id = GraphSession().addFlowrule(self._session_id, pfr.get_switch_id(), flow_rule, None)
        self.__ODL_VlanTraking_add(pfr, flow_rule_db_id)
    
    
    
    
    
    def __ODL_VlanTraking_add(self, pfr, flow_rule_db_id):
        vlan_in = None
        vlan_out = None
        port_in = None
        port_out = None
        switch_id = pfr.get_switch_id()
        
        if(pfr.get_match().input_port is not None):
            port_in = pfr.get_match().input_port
        
        if(pfr.get_match().vlan_id is not None):
            vlan_in = pfr.get_match().vlan_id
            vlan_out = vlan_in
        
        for a in pfr.get_actions():
            if(a.action_type=="output-action"):
                port_out = a.output_port
            if(a.action_type=="vlan-match"):
                vlan_out = a.vlan_id
            elif(a.action_type=="pop-vlan-action"):
                vlan_out = None
        
        # DATABASE: Add vlan tracking
        GraphSession().vlanTracking_add(flow_rule_db_id, switch_id,vlan_in,port_in,vlan_out,port_out)

    
    
    
    
    def __ODL_GetLinkBetweenSwitches(self, switch1, switch2):             
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


    
    
    
    def __ODL_GetLinkPortsBetweenSwitches(self, switch1, switch2):
        link = self.__ODL_GetLinkBetweenSwitches(switch1, switch2)
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





    def __ODL_LinkEndpoints(self,path,ep1,ep2,flowrule):

        pfr = OpenDayLightCA.__processedFLowrule(flow_id=flowrule.id, priority=flowrule.priority)
        base_actions = []
        vlan_id = None
        
        print ""
        print "Flow id: "+str(pfr.get_flow_id())
        print "Flow priority: "+str(pfr.get_priority())        
        
        
        # Clean actions
        for a in flowrule.actions:
            
            # Store the VLAN ID and remove the action
            if a.set_vlan_id is not None:
                vlan_id = a.set_vlan_id
                continue
            
            # Filter non OUTPUT actions 
            if a.output is None:
                no_output = Action(a)
                base_actions.append(no_output)
                
        
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
            pfr.set_vlan_id(vlan_id)
        
        
        # Traverse the path and create the flow for each switch
        for i in range(0, len(path)):
            hop = path[i]
            
            pfr.set_flow_name(i)
            base_match = Match(flowrule.match)
            pfr.set_actions(list(base_actions))
            
            if i==0:
                #first switch
                pfr.set_switch_id(ep1.switch_id)
                port_in = ep1.interface
                port_out = self.netgraph.topology[hop][path[i+1]]['from_port']
                
                if vlan_id is not None:
                    action_pushvlan = Action()
                    action_pushvlan.setPushVlanAction()
                    pfr.append_action(action_pushvlan)
                    
                    action_setvlan = Action()
                    action_setvlan.setSwapVlanAction(vlan_id)
                    pfr.append_action(action_setvlan)
                
            elif i==len(path)-1:
                #last switch
                pfr.set_switch_id(ep2.switch_id)
                port_in = self.netgraph.topology[path[i-1]][hop]['to_port']
                port_out = ep2.interface
                
                if vlan_id is not None:
                    base_match.setVlanMatch(vlan_id)
                    action_stripvlan = Action()
                    action_stripvlan.setPopVlanAction()
                    pfr.append_action(action_stripvlan)

            else:
                #middle way switch
                pfr.set_switch_id(hop)
                port_in = self.netgraph.topology[path[i-1]][hop]['to_port']
                port_out = self.netgraph.topology[hop][path[i+1]]['from_port']
                
                if vlan_id is not None:
                    base_match.setVlanMatch(vlan_id)
                
            print pfr.get_switch_id()+" from "+str(port_in)+" to "+str(port_out)
            
            base_match.setInputMatch(port_in)
            pfr.set_match(base_match)
            
            action_output = Action()
            action_output.setOutputAction(port_out, 65535)
            pfr.append_action(action_output)
            
            self.__ODL_PushFlow(pfr)
        
        # end-for
        
        return


