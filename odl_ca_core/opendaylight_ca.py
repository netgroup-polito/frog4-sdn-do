'''
@author: fabiomignini
@author: vida
@author: giacomoratta
'''

from __future__ import division
import logging, json

from nffg_library.nffg import FlowRule, Match as NffgMatch, Action as NffgAction

from odl_ca_core.sql.graph_session import GraphSession

from odl_ca_core.config import Configuration
from odl_ca_core.odl_rest import ODL_Rest
from odl_ca_core.resources import Action, Match, Flow, ProfileGraph, Endpoint
from odl_ca_core.netgraph import NetGraph
from odl_ca_core.exception import sessionNotFound, GraphError, NffgUselessInformations, NffgInvalidActions






class OpenDayLightCA(object):

    def __init__(self, user_data):
        
        conf = Configuration()
        
        self.__session_id = None
        
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
            return self.__session_id
            
        # Instantiate a new NF-FG
        try:
            logging.debug("Put NF-FG: instantiating a new nffg: " + nffg.getJSON(True))
            self.__session_id = GraphSession().addNFFG(nffg, self.user_data.user_id)
            
            # Send flow rules to ODL by profile_graph
            profile_graph = self.__ProfileGraph_BuildFromNFFG(nffg)
            self.__ODL_FlowsInstantiation(profile_graph)
            logging.debug("Put NF-FG: session " + self.__session_id + " correctly instantiated!")

            GraphSession().updateStatus(self.__session_id, 'complete')
            
        except Exception as ex:
            logging.error(ex)
            self.__deleteGraph()
            GraphSession().setErrorStatus(self.__session_id)
            raise ex                           
        return self.__session_id

    
    
    def NFFG_Update(self, new_nffg):

        # Check and get the session id for this user-graph couple
        logging.debug("Update NF-FG: check if the user "+self.user_data.user_id+" has already instantiated the graph "+new_nffg.id+".")
        session = GraphSession().getActiveSession(self.user_data.user_id, new_nffg.id, error_aware=True)
        if session is None:
            return None
        self.__session_id = session.session_id
        logging.debug("Update NF-FG: already instantiated, trying to update it")
        
        try:
            logging.debug("Update NF-FG: updating session "+self.__session_id+" from user "+self.user_data.username+" on tenant "+self.user_data.tenant)
            GraphSession().updateStatus(self.__session_id, 'updating')
    
            # Get the old NFFG
            old_nffg = GraphSession().getNFFG(self.__session_id)
            logging.debug("Update NF-FG: the old session: "+old_nffg.getJSON())
            
            # Get the updated NFFG
            updated_nffg = old_nffg.diff(new_nffg)
            logging.debug("Update NF-FG: coming updates: "+updated_nffg.getJSON(True))            
            
            # Delete useless endpoints and flowrules 
            self.__NFFG_Update__deletions(updated_nffg)
            
            # Update database
            GraphSession().updateNFFG(updated_nffg, self.__session_id)
            
            # Send flowrules to ODL by profile_graph
            profile_graph = self.__ProfileGraph_BuildFromNFFG(updated_nffg)
            self.__ODL_FlowsInstantiation(profile_graph)
            logging.debug("Update NF-FG: session " + self.__session_id + " correctly updated!")
            
            GraphSession().updateStatus(self.__session_id, 'complete')
            
        except Exception as ex:
            logging.error("Update NF-FG: ",ex)
            self.__deleteGraph()
            GraphSession().setErrorStatus(self.__session_id)
            raise ex
        return self.__session_id

    
    
    def NFFG_Delete(self, nffg_id):
        
        session = GraphSession().getActiveSession(self.user_data.user_id, nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Delete NF-FG: session not found for graph "+str(nffg_id))
        self.__session_id = session.session_id

        try:
            instantiated_nffg = GraphSession().getNFFG(self.__session_id)
            logging.debug("Delete NF-FG: [session="+str(self.__session_id)+"] we are going to delete: "+instantiated_nffg.getJSON())
            self.__deleteGraph()
            logging.debug("Delete NF-FG: session " + self.__session_id + " correctly deleted!")
            
        except Exception as ex:
            logging.error("Delete NF-FG: ",ex)
            raise ex
        

    
    def NFFG_Get(self, nffg_id):
        session = GraphSession().getActiveSession(self.user_data.user_id, nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Get NF-FG: session not found, for graph "+str(nffg_id))
        
        self.__session_id = session.session_id
        logging.debug("Getting session: "+str(self.__session_id))
        return GraphSession().getNFFG(self.__session_id).getJSON()


    
    def NFFG_Status(self, nffg_id):
        session = GraphSession().getActiveSession(self.user_data.user_id,nffg_id,error_aware=True)
        if session is None:
            raise sessionNotFound("Status NF-FG: session not found, for graph "+str(nffg_id))
        
        self.__session_id = session.session_id
        logging.debug("Status NF-FG: graph status: "+str(session.status))
        return session.status
    
    
    
    def NFFG_Validate(self, nffg):
        '''
        A validator for this specific control adapter.
        The original json, as specified in the extern NFFG library,
        could contain useless objects and fields for this CA.
        If this happens, we have to raise exceptions to stop the request processing.  
        '''
        # VNFs inspections
        if len(nffg.vnfs)>0:
            msg = "NFFG Validation: presence of 'VNFs'. This CA does not process this information."
            logging.debug(msg)
            raise NffgUselessInformations(msg)
        
        # END POINTs inspections
        for ep in nffg.end_points:
            if(ep.remote_endpoint_id is not None):
                msg = "NFFG Validation: presence of 'end-points.remote_endpoint_id'. This CA does not process this information."
                logging.debug(msg)
                raise NffgUselessInformations(msg)
            if(ep.remote_ip is not None):
                msg = "NFFG Validation: presence of 'end-points.remote-ip'. This CA does not process this information."
                logging.debug(msg)
                raise NffgUselessInformations(msg)
            if(ep.type != "interface"):
                msg = "NFFG Validation: 'end-points.type' must be 'interface'."
                logging.debug(msg)
                raise NffgUselessInformations(msg)

        # FLOW RULEs inspection
        for flowrule in nffg.flow_rules:

            # Detect multiple output actions (they are not allowed).
            # If multiple output are needed, multiple flow rules should be written
            # in the nffg.json, with a different priorities!
            output_action_counter=0
            for a in flowrule.actions:
                if a.output is not None:
                    if output_action_counter > 0:
                        msg = "NFFG Validation: not allowed 'multiple output' (flow rule "+flowrule.id+")."
                        logging.debug(msg)
                        raise NffgInvalidActions(msg)
                    output_action_counter = output_action_counter+1
                    
                



    '''
    ######################################################################################################
    #########################    Interactions with OpenDaylight              #############################
    ######################################################################################################
    '''

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
            
            ep = Endpoint(endpoint.id, endpoint.name, endpoint.type, endpoint.vlan_id, endpoint.switch_id, endpoint.interface, status)
            profile_graph.addEndpoint(ep)
        
        for flowrule in nffg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            profile_graph.addFlowrule(flowrule)
                  
        return profile_graph
    
    
    
    
    
    def __NFFG_Update__deletions(self, updated_nffg):
        
        def getEndpointID(endpoint_string):
            if endpoint_string is None:
                return None
            endpoint_string = str(endpoint_string)
            tmp2 = endpoint_string.split(':')
            port2_type = tmp2[0]
            port2_id = tmp2[1]
            if port2_type == 'endpoint':
                return port2_id
            return None
        
        # List of updated endpoints
        updated_endpoints = []
        
        # Delete the endpoints 'to_be_deleted'
        for endpoint in updated_nffg.end_points:
            if endpoint.status == 'to_be_deleted':
                self.__deleteEndpointByGraphID(endpoint.id)
                updated_nffg.end_points.remove(endpoint)
            elif endpoint.status == 'new':
                updated_endpoints.append(endpoint.id)
        
        # Delete the flowrules 'to_be_deleted'
        # "[:]" keep in memory deleted items during the loop.
        for flowrule in updated_nffg.flow_rules[:]:
            
            # Delete flowrule
            if flowrule.status == 'to_be_deleted': #and flowrule.type != 'external':
                self.__deleteFlowRuleByGraphID(flowrule.id)
                updated_nffg.flow_rules.remove(flowrule)
            
            # Set flowrule as "new" when associated endpoint has been updated
            elif flowrule.status == 'already_deployed':
                ep_in = getEndpointID(flowrule.match.port_in)
                if ep_in is not None and ep_in in updated_endpoints:
                    flowrule.status = 'new'
                else:
                    for a in  flowrule.actions:
                        ep_out = getEndpointID(a.output)
                        if ep_out is not None and ep_out in updated_endpoints:
                            flowrule.status = 'new'





    def __ODL_FlowsInstantiation(self, profile_graph):

        # Create and push the flowrules
        for flowrule in profile_graph.flowrules.values():
            
            #TODO: check priority

            # Flow rule checks
            if flowrule.status !='new':
                continue                
            if flowrule.match is None:
                continue            
            if flowrule.match.port_in is None:
                continue
            
            # Endpoint checks
            tmp1 = flowrule.match.port_in.split(':')
            port1_type = tmp1[0]
            port1_id = tmp1[1]
            if port1_type != 'endpoint':
                continue
            endp1 = profile_graph.endpoints[port1_id]
            if endp1.type != 'interface':
                continue
            
            # Process flow rule with VLAN
            self.__ODL_ProcessFlowrule(endp1, flowrule, profile_graph)
    
    
    
    

    def __deleteFlowRuleByGraphID(self, graph_flow_rule_id):
        flowrules = GraphSession().getFlowrules(self.__session_id, graph_flow_rule_id)
        if flowrules is not None:
            for fr in flowrules:
                self.__deleteFlowRule(fr)
    
    def __deleteFlowRuleByID(self, flow_rule_id):
        fr = GraphSession().getFlowruleByID(flow_rule_id)
        if fr is None:
            return
        if fr.internal_id is not None and fr.type is not None:
            self.__deleteFlowRule(fr)
        self.__deleteFlowRuleByGraphID(fr.graph_flow_rule_id)
    
    def __deleteFlowRule(self, flow_rule):
        # flow_rule is a FlowRuleModel object
        if flow_rule.type == 'external': #and flow.status == "complete" 
            ODL_Rest(self.odlversion).deleteFlow(self.odlendpoint, self.odlusername, self.odlpassword, flow_rule.switch_id, flow_rule.internal_id)
        GraphSession().deleteFlowrule(flow_rule.id)

    
    def __deletePortByID(self, port_id):
        GraphSession().deletePort(port_id)

       
    def __deleteEndpointByGraphID(self, graph_endpoint_id):
        ep = GraphSession().getEndpointByGraphID(graph_endpoint_id, self.__session_id)
        if ep is not None:
            self.__deleteEndpointByID(ep.id)

    def __deleteEndpointByID(self, endpoint_id):
        ep_resources = GraphSession().getEndpointResources(endpoint_id)
        if ep_resources is None:
            return
        for eprs in ep_resources:
            if eprs.resource_type == 'flow-rule':
                self.__deleteFlowRuleByID(eprs.resource_id)
            elif eprs.resource_type == 'port':
                self.__deletePortByID(eprs.resource_id)
        GraphSession().deleteEndpoint(endpoint_id)
    
    
    def __deleteGraph(self):
        # Endpoints
        endpoints = GraphSession().getEndpointsBySessionID(self.__session_id)
        if endpoints is not None:
            for ep in endpoints:
                self.__deleteEndpointByID(ep.id)
        # Flowrules (maybe will never enter)
        flowrules = GraphSession().getFlowrules(self.__session_id)
        if flowrules is None:
            for fr in flowrules:
                self.__deleteFlowRule(fr)
        # End field
        GraphSession().setEnded(self.__session_id)
        
        
        




    




    def __ODL_ProcessFlowrule(self, in_endpoint, flowrule, profile_graph):
        '''
        Process a flow rule written in the section "big switch" of a nffg json.
        Add a vlan match/mod/strip to every flowrule in order to distinguish it.
        After the verification that output is an endpoint, this function manages
        three main cases:
            1) endpoints are on the same switch;
            2) endpoints are on different switches directly linked;
            3) endpoints are on different switches not directly linked, so search for a path.
        '''
        
        # TODO: check "vlan in" match on in_endpoint
        if GraphSession().vlanInIsBusy(in_endpoint.switch_id, flowrule.match.vlan_id, in_endpoint.interface):
            raise GraphError("Flowrule "+flowrule.id+" use a busy vlan id "+flowrule.match.vlan_id+" on the same port in (ingress endpoint "+in_endpoint.id+")")

        def getEndpointID(output_string):
            tmp2 = output_string.split(':')
            port2_type = tmp2[0]
            port2_id = tmp2[1]
            if port2_type == 'endpoint':
                return port2_id
            return None
        
        fr1 = OpenDayLightCA.__externalFlowrule( match=Match(flowrule.match), priority=flowrule.priority, flow_id=flowrule.id, nffg_flowrule=flowrule)
        fr2 = OpenDayLightCA.__externalFlowrule( priority=flowrule.priority, flow_id=flowrule.id, nffg_flowrule=flowrule)
        out_endpoint = None
        nodes_path = None
        
        # Add "Drop" flow rules only, and return.
        # If a flow rule has a drop action, we don't care other actions!
        for a in flowrule.actions:
            if a.drop is True:
                fr1.setFr1(in_endpoint.switch_id, a, in_endpoint.interface , None, "1")
                self.__Push_externalFlowrule(fr1)
                return  
        
        # Split the action handling in output and non-output.
        for a in flowrule.actions:
            
            # If this action is not an output action,
            # we just append it to the final actions list 'actions1'.
            if a.output is None:
                no_output = Action(a)
                fr1.append_action(no_output)
                continue
            
            # If this action is an output action (a.output is not None),
            # we check that the output is an endpoint and manage the main cases.

            # Is the 'output' destination an endpoint?
            port2_id = getEndpointID(a.output)
            if port2_id is None:
                continue
            out_endpoint = profile_graph.endpoints[port2_id] #Endpoint object (declared in resources.py)


            # [ 1 ] Endpoints are on the same switch
            if in_endpoint.switch_id == out_endpoint.switch_id:
                
                # Error: endpoints are equal!
                if in_endpoint.interface == out_endpoint.interface:
                    raise GraphError("Flowrule "+flowrule.id+" is wrong: endpoints are overlapping")
                
                # Install a flow between two ports of the switch
                fr1.setFr1(in_endpoint.switch_id, a, in_endpoint.interface , out_endpoint.interface, "1")
                continue


            # [ 2 ] Endpoints are on different switches directly linked
            # Check if a link between endpoint switches exists.
            # Return: port12 (on in_endpoint switch) and port21 (on out_endpoint switch).
            port12,port21 = self.__ODL_GetLinkPortsBetweenSwitches(in_endpoint.switch_id, out_endpoint.switch_id)       
            if port12 is not None and port21 is not None:

                # Endpoints are not on the link: 2 flows (most probable setup) 
                if in_endpoint.interface != port12 and out_endpoint.interface != port21:
                    fr1.setFr1(in_endpoint.switch_id, a, in_endpoint.interface , port12, "1")
                    fr2.setFr1(out_endpoint.switch_id, None, port21 , out_endpoint.interface, "2")
                    continue
                           
                # One or both endpoints interfaces overlap the ports of the link!
                else:
                    logging.warning("Flow not installed for flowrule id "+flowrule.id+": "+
                                    "one or both endpoints are on the same link "+
                                    "[ ("+in_endpoint.interface+","+port12+");("+out_endpoint.interface+","+port21+")]")


            # [ 3 ] Endpoints are on different switches not directly linked...search for a path!
            nodes_path = self.netgraph.getShortestPath(in_endpoint.switch_id, out_endpoint.switch_id)
            if(nodes_path is not None):
                logging.info("Found a path bewteen "+in_endpoint.switch_id+" and "+out_endpoint.switch_id+". "+"Path Length = "+str(len(nodes_path)))
            else:
                logging.debug("Cannot find a link between "+in_endpoint.switch_id+" and "+out_endpoint.switch_id)
        
        # <-- End-for on "flowrule.actions" array 
        
        # Push the fr1, if it is ready                
        if fr1.isReady():
            self.__Push_externalFlowrule(fr1)
        
            # Push the fr2, if it is ready
            if fr2.isReady():
                self.__Push_externalFlowrule(fr2)
        
        # There is a path between the two endpoint
        if nodes_path is not None:
            self.__ODL_LinkEndpointsByVlanID(nodes_path, in_endpoint, out_endpoint, flowrule)





    def __ODL_LinkEndpointsByVlanID(self, path, ep1, ep2, flowrule):
        
        ''' 
        This function links two endpoints with a set of flow rules pushed in
        all the intermediate switches (and in first and last switches, of course).
        
        The link between this endpoints is based on vlan id.
        If no ingress (or egress) vlan id is specified, a suitable vlan id will be chosen.
        In any case, all the vlan ids will be checked in order to avoid possible 
        conflicts in the traversed switches.
        '''

        efr = OpenDayLightCA.__externalFlowrule(flow_id=flowrule.id, priority=flowrule.priority, nffg_flowrule=flowrule)
        
        base_actions = []
        vlan_out = None
        original_vlan_out = None
        vlan_in = None
        
        # Initialize vlan_id and save it
        if flowrule.match.vlan_id is not None:
            vlan_in = flowrule.match.vlan_id
            original_vlan_out = vlan_in
        
        # Clean actions and search for an egress vlan id
        for a in flowrule.actions:
            
            # Store the VLAN ID and remove the action
            if a.set_vlan_id is not None:
                vlan_out = a.set_vlan_id
                original_vlan_out = a.set_vlan_id
                continue
            
            # Filter non OUTPUT actions 
            if a.output is None:
                no_output = Action(a)
                base_actions.append(no_output)
        
        # Detect if it is a mod/strip flow
        is_mod_strip_flow = (vlan_in is None)
        
        # Traverse the path and create the flow for each switch
        for i in range(0, len(path)):
            hop = path[i]
            efr.set_flow_name(i)
            base_match = Match(flowrule.match)
            efr.set_actions(list(base_actions))
            
            # Switch position
            pos = 0 # (-1:first, 0:middle, 1:last)
            
            # Next switch and next ingress port
            next_switch_ID = None
            next_switch_portIn = None
            if i < (len(path)-1):
                next_switch_ID = path[i+1]
                next_switch_portIn = self.netgraph.switchPortIn(next_switch_ID, hop)
            
            # First switch
            if i==0:
                pos = -1
                efr.set_switch_id(ep1.switch_id)
                port_in = ep1.interface
                port_out = self.netgraph.switchPortOut(hop, next_switch_ID)
            
            # Last switch
            elif i==len(path)-1:
                pos = 1
                efr.set_switch_id(ep2.switch_id)
                port_in = self.netgraph.switchPortIn(hop, path[i-1])
                port_out = ep2.interface
                # Force the vlan out to be equal to the original
                if is_mod_strip_flow == False and original_vlan_out is not None:
                    vlan_out = original_vlan_out 
            
            # Middle way switch
            else:
                efr.set_switch_id(hop)
                port_in = self.netgraph.switchPortIn(hop, path[i-1])
                port_out = self.netgraph.switchPortOut(hop, next_switch_ID)
            
            # Check, generate and set vlan ids
            vlan_in, vlan_out, set_vlan_out = self.__ODL_VlanTraking_check(port_in, port_out, vlan_in, vlan_out, next_switch_ID, next_switch_portIn)
            
            # Match
            if vlan_in is not None:
                base_match.setVlanMatch(vlan_in)

            # Add/mod VLAN header
            if set_vlan_out is not None:
                
                # If there is a match rule on vlan id, it means a vlan header 
                # it is already present and we do not need to push a vlan.
                if vlan_in is None:
                    action_pushvlan = Action()
                    action_pushvlan.setPushVlanAction()
                    efr.append_action(action_pushvlan)
                    
                action_setvlan = Action()
                action_setvlan.setSwapVlanAction(set_vlan_out)
                efr.append_action(action_setvlan)
            
            # Remove VLAN header
            elif is_mod_strip_flow and pos==1:
                action_stripvlan = Action()
                action_stripvlan.setPopVlanAction()
                efr.append_action(action_stripvlan)
            
            # Set next ingress vlan
            vlan_in = vlan_out
                
            print("["+efr.get_flow_name()+"] "+efr.get_switch_id()+" from "+str(port_in)+" to "+str(port_out))
            
            # Push the flow rule
            base_match.setInputMatch(port_in)
            efr.set_match(base_match)
            action_output = Action()
            action_output.setOutputAction(port_out, 65535)
            efr.append_action(action_output)
            self.__Push_externalFlowrule(efr)
        # end-for
        '''
        Note#1 - Where are the original vlan id?
            vlan in = flowrule.match.vlan_id
            vlan out = original_vlan_out
        '''
        return





    
    
    
    
    
    
    def __ODL_VlanTraking_add(self, efr, flow_rule_db_id):
        # efr = __externalFlowrule
        vlan_in = None
        vlan_out = None
        port_in = None
        port_out = None
        switch_id = efr.get_switch_id()
        
        if(efr.get_match().input_port is not None):
            port_in = efr.get_match().input_port
        
        if(efr.get_match().vlan_id is not None):
            vlan_in = efr.get_match().vlan_id
            vlan_out = vlan_in
        
        for a in efr.get_actions():
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





    def __ODL_VlanTraking_check(self, port_in, port_out, vlan_in=None, vlan_out=None, next_switch_ID=None, next_switch_portIn=None):
        
        # Rectify vlan ids
        if vlan_in is not None:
            vlan_in = int(vlan_in)
        if vlan_out is not None:
            vlan_out = int(vlan_out)
        if vlan_out is not None and ( vlan_out<=0 or vlan_out>=4095 ):
            vlan_out = None
        if vlan_in is not None and ( vlan_in<=0 or vlan_in>=4095 ):
            vlan_in = None
            
        # Detect if a mod_vlan action is needed
        set_vlan_out = None
        if vlan_out is not None and vlan_out != vlan_in:
            set_vlan_out = vlan_out
        
        # Set the output vlan that we have to check in the next switch
        if vlan_in is not None and vlan_out is None:
            vlan_out = vlan_in
        
        # Verify this output vlan id
        if vlan_out is not None and next_switch_ID is not None:
            #check vlan output in next switch-port / return None if non suitable
            #vlan_out = GraphSession().vlanTracking_check(port_in,port_out,vlan_in,vlan_out,next_switch_ID,next_switch_portIn)
            if GraphSession().vlanInIsBusy(next_switch_ID, vlan_out, next_switch_portIn):
                vlan_out = None

        # Check if an output vlan id is needed
        if vlan_out is None and next_switch_ID is not None:
            #generate for the next switch-port
            # TODO: manage the '0' value (error) and '-1' value (all vlan ids are busy)
            vlan_out = GraphSession().vlanTracking_new_vlan_out(port_in,port_out,vlan_in,vlan_out,next_switch_ID,next_switch_portIn) 
            set_vlan_out = vlan_out
        
        return vlan_in, vlan_out, set_vlan_out
    
    
    
    

    def __Push_externalFlowrule(self, efr):
        # efr = __externalFlowrule
        '''
        This is the only function that should be used to push an external flow
        (a "custom flow", in other words) in the database and in the opendaylight controller.
        GraphSession().addFlowrule(...) is also used in GraphSession().updateNFFG 
        and in GraphSession().addNFFG to store the flow rules written in nffg.json.
        '''
        
        '''
        TODO: store entire flowrule in the database
        def __ODL_ExternalFlowrule_Exists(self, switch, nffg_match, nffg_action):
        
        TODO: check if a "similar" flow rule already exists in the specified switch.
        Similar flow rules are replaced by ovs switch, so one of them disappear!
        
        If exists, we should:
            1) change the priority and push flow rule, or
            2) replace with new flow rule, or
            3) extend the old flow rule with the new flow rule charateristics (action/match)
        
        In the third case ("joined flow rules"), ...
        '''

        # ODL/Switch: Add flow rule
        flowj = Flow("flowrule", efr.get_flow_name(), 0, efr.get_priority(), True, 0, 0, efr.get_actions(), efr.get_match())
        json_req = flowj.getJSON(self.odlversion, efr.get_switch_id())
        ODL_Rest(self.odlversion).createFlow(self.odlendpoint, self.odlusername, self.odlpassword, json_req, efr.get_switch_id(), efr.get_flow_name())
        
        # DATABASE: Add flow rule
        flow_rule = FlowRule(_id=efr.get_flow_id(),node_id=efr.get_switch_id(), _type='external', status='complete',
                             priority=efr.get_priority(), internal_id=efr.get_flow_name())
        flow_rule_db_id = GraphSession().addFlowrule(self.__session_id, efr.get_switch_id(), flow_rule)
        GraphSession().dbStoreMatch(efr.getNffgMatch(), flow_rule_db_id, flow_rule_db_id)
        GraphSession().dbStoreAction(efr.getNffgAction(), flow_rule_db_id)
        
        # DATABASE: Add vlan tracking
        self.__ODL_VlanTraking_add(efr, flow_rule_db_id)
    

    
    class __externalFlowrule(object):
        '''
        Private class used to store an external flow rule
        that is going to be pushed in the specified switch.
        '''
        def __init__(self,switch_id=None,match=None,actions=None,flow_id=None,priority=None,flowname_suffix=None,nffg_flowrule=None):
            self.__switch_id = switch_id
            self.set_flow_id(flow_id)
            self.set_flow_name(flowname_suffix)
            self.__priority = priority
            
            # match = resources.Match object
            self.__match = match
            
            # actions = array of resources.Action object
            self.set_actions(actions)
            
            # nffg_flowrule = nffg.FlowRule object
            # (usually not used, but useful in some cases)
            self.__nffg_flowrule = nffg_flowrule
            

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
        
        
        def getNffgMatch(self):
            
            port_in = self.__match.input_port
            ether_type = self.__match.ethertype
            vlan_id = self.__match.vlan_id
            source_mac = self.__match.eth_source
            dest_mac = self.__match.eth_dest
            source_ip = self.__match.ip_source
            dest_ip = self.__match.ip_dest
            source_port = self.__match.port_source
            dest_port = self.__match.port_dest
            protocol = self.__match.ip_protocol
            
            # Not directly supported fields
            tos_bits = self.__nffg_flowrule.match.tos_bits
            vlan_priority = self.__nffg_flowrule.match.vlan_priority
            db_id = None
            
            return NffgMatch(port_in=port_in, ether_type=ether_type, 
                             vlan_id=vlan_id, vlan_priority=vlan_priority,
                             source_mac=source_mac, dest_mac=dest_mac, 
                             source_ip=source_ip, dest_ip=dest_ip, 
                             tos_bits=tos_bits,
                             source_port=source_port, dest_port=dest_port,
                             protocol=protocol, db_id=db_id)
            
            
        def getNffgAction(self):
            
            output = None
            controller = False
            drop = False
            set_vlan_id = None
            pop_vlan = False
            set_ethernet_src_address = None
            set_ethernet_dst_address = None
            
            # Not supported fields
            set_vlan_priority = None
            set_ip_src_address = None 
            set_ip_dst_address= None
            set_ip_tos = None
            set_l4_src_port=None
            set_l4_dst_port = None
            output_to_queue= None
            
            # Compress all actions in a single NffgAction (for dbStoreAction)
            # Multiple output not allowed
            for a in self.__actions:
                if a.is_output_port_action():
                    output = a.output_port
                elif a.is_output_controller_action():
                    controller = True
                elif a.is_drop_action():
                    drop = True
                elif a.is_set_vlan_action():
                    set_vlan_id = a.vlan_id
                elif a.is_pop_vlan_action():
                    pop_vlan = True
                elif a.is_eth_src_action():
                    set_ethernet_src_address = a.address
                elif a.is_eth_dst_action():
                    set_ethernet_dst_address = a.address

            return NffgAction(output = output, controller = controller, drop = drop, 
                              set_vlan_id = set_vlan_id, set_vlan_priority = set_vlan_priority, pop_vlan = pop_vlan,
                              set_ethernet_src_address = set_ethernet_src_address, set_ethernet_dst_address= set_ethernet_dst_address,
                              set_ip_src_address = set_ip_src_address, set_ip_dst_address = set_ip_dst_address,
                              set_ip_tos = set_ip_tos, set_l4_src_port = set_l4_src_port, set_l4_dst_port = set_l4_dst_port, 
                              output_to_queue = output_to_queue, db_id = None)

