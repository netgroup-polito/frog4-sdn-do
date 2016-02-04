'''
@author: fabiomignini
@author: vida
@author: giacomoratta
'''

from __future__ import division
import logging

from nffg_library.nffg import FlowRule as NffgFlowrule

from do_core.sql.graph_session import GraphSession

from do_core.config import Configuration
from do_core.resource_description import ResourceDescription
from do_core.netmanager import NetManager, Match ,Action
from do_core.messaging import Messaging
from do_core.exception import sessionNotFound, GraphError, NffgUselessInformations
from requests.exceptions import HTTPError



class OpenDayLightDO(object):

    def __init__(self, user_data):

        self.__session_id = None
        
        self.nffg = None
        self.user_data = user_data
        '''
        Fields:
         - user_data.username
         - user_data.password
         - user_data.tenant
        '''
        
        # NetManager
        self.NetManager = NetManager()


    
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
            
            # Send flow rules to ODL
            self.__ODL_FlowsInstantiation(nffg)
            logging.debug("Put NF-FG: session " + self.__session_id + " correctly instantiated!")

            GraphSession().updateStatus(self.__session_id, 'complete')
            
            # Update the resource description .json
            ResourceDescription().updateAll()
            ResourceDescription().saveFile()
            
            Messaging().PublishDomainConfig()
            
            return self.__session_id
        
        except Exception as ex:
            logging.error(ex)
            self.__NFFG_ODL_deleteGraph()
            GraphSession().updateError(self.__session_id)
            raise ex                           
        

    
    
    def NFFG_Update(self, new_nffg):

        # Check and get the session id for this user-graph couple
        logging.debug("Update NF-FG: check if the user "+self.user_data.user_id+" has already instantiated the graph "+new_nffg.id+".")
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, new_nffg.id, error_aware=True)
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
            
            # Delete useless endpoints and flowrules, from DB and ODL 
            self.__NFFG_ODL_DeleteAndUpdate(updated_nffg)
            
            # Update database
            GraphSession().updateNFFG(updated_nffg, self.__session_id)
            
            # Send flowrules to ODL
            self.__ODL_FlowsInstantiation(updated_nffg)
            logging.debug("Update NF-FG: session " + self.__session_id + " correctly updated!")
            
            GraphSession().updateStatus(self.__session_id, 'complete')
            
            # Update the resource description .json
            ResourceDescription().updateAll()
            ResourceDescription().saveFile()
            
            Messaging().PublishDomainConfig()
            
        except Exception as ex:
            logging.error("Update NF-FG: ",ex)
            self.__NFFG_ODL_deleteGraph()
            GraphSession().updateError(self.__session_id)
            raise ex
        return self.__session_id

    
    
    def NFFG_Delete(self, nffg_id):
        
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, nffg_id, error_aware=False)
        if session is None:
            raise sessionNotFound("Delete NF-FG: session not found for graph "+str(nffg_id))
        self.__session_id = session.session_id

        try:
            instantiated_nffg = GraphSession().getNFFG(self.__session_id)
            logging.debug("Delete NF-FG: [session="+str(self.__session_id)+"] we are going to delete: "+instantiated_nffg.getJSON())
            self.__NFFG_ODL_deleteGraph()
            logging.debug("Delete NF-FG: session " + self.__session_id + " correctly deleted!")
            
            # Update the resource description .json
            ResourceDescription().updateAll()
            ResourceDescription().saveFile()
            
            Messaging().PublishDomainConfig()
            
        except Exception as ex:
            logging.error("Delete NF-FG: ",ex)
            raise ex
        

    
    def NFFG_Get(self, nffg_id):
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id, nffg_id, error_aware=True)
        if session is None:
            raise sessionNotFound("Get NF-FG: session not found, for graph "+str(nffg_id))
        
        self.__session_id = session.session_id
        logging.debug("Getting session: "+str(self.__session_id))
        return GraphSession().getNFFG(self.__session_id).getJSON()


    
    def NFFG_Status(self, nffg_id):
        session = GraphSession().getActiveUserGraphSession(self.user_data.user_id,nffg_id,error_aware=False)
        if session is None:
            raise sessionNotFound("Status NF-FG: session not found, for graph "+str(nffg_id))
        
        self.__session_id = session.session_id
        percentage = 0
        
        if session.status != 'error':
            percentage = GraphSession().getFlowruleProgressionPercentage(self.__session_id,nffg_id)
        
        logging.debug("Status NF-FG: graph status: "+str(session.status)+" "+str(percentage)+"%")
        return session.status,percentage
    
    
    
    def NFFG_Validate(self, nffg):
        '''
        A validator for this specific domain orchestrator.
        The original json, as specified in the extern NFFG library,
        could contain useless objects and fields for this DO.
        If this happens, we have to raise exceptions to stop the request processing.  
        '''
        
        def raise_useless_info(msg):
            logging.debug("NFFG Validation: "+msg+". This DO does not process this kind of data.")
            raise NffgUselessInformations("NFFG Validation: "+msg+". This DO does not process this kind of data.")
        
        def raise_invalid_actions(msg):
            logging.debug("NFFG Validation: "+msg+". This DO does not process this kind of flowrules.")
            raise NffgUselessInformations("NFFG Validation: "+msg+". This DO does not process this kind of flowrules.")
        
        
        # VNFs inspections
        if len(nffg.vnfs)>0:
            raise_useless_info("presence of 'VNFs'")
            
        '''
        Busy VLAN ID: the control on the required vlan id(s) must wait for
        the graph instantiation into the database in order to clarify the situation.
        Finally, the the control on the required vlan id(s) is always made before
        processing a flowrule (see the first rows of "__ODL_ProcessFlowrule").
        '''
        
        # END POINTs inspections
        for ep in nffg.end_points:
            if(ep.type is not None and ep.type != "interface" and ep.type != "vlan"):
                raise_useless_info("'end-points.type' must be 'interface' or 'vlan' (not '"+ep.type+"')")
            if ep.node_id is not None:
                raise_useless_info("presence of 'node-id'")
            if(ep.remote_endpoint_id is not None):
                raise_useless_info("presence of 'end-points.remote_endpoint_id'")
            if(ep.remote_ip is not None):
                raise_useless_info("presence of 'end-points.remote-ip'")
            if(ep.local_ip is not None):
                raise_useless_info("presence of 'end-points.local-ip'")
            if ep.gre_key is not None:
                raise_useless_info("presence of 'gre-key'")
            if ep.ttl is not None:
                raise_useless_info("presence of 'ttl'")
            if ep.prepare_connection_to_remote_endpoint_id is not None:
                raise_useless_info("presence of connection to remote endpoint")
            if ep.prepare_connection_to_remote_endpoint_ids is not None and len(ep.prepare_connection_to_remote_endpoint_ids)>0:
                raise_useless_info("presence of connection to remote endpoints")
                
            # Check endpoints in ResourceDescription.json (switch/port)
            if ResourceDescription().checkEndpoint(ep.switch_id, ep.interface)==False:
                raise GraphError("Endpoint "+ep.id+" not found")
            
            # Check vlan availability
            if ep.type == "vlan" and ep.vlan_id is not None:
                if ResourceDescription().VlanID_isAvailable(int(ep.vlan_id))==False:
                    vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                    raise GraphError("Vlan ID "+str(ep.vlan_id)+" not allowed! Valid vlan ids: "+vids_list)
                

        # FLOW RULEs inspection
        for flowrule in nffg.flow_rules:
         
            if flowrule.match is None:
                GraphError("Flowrule "+flowrule.id+" has not match section")
            if flowrule.match.port_in is None:
                GraphError("Flowrule "+flowrule.id+" has not an ingress endpoint ('port_in')")
            if self.__getEndpointIdFromString(flowrule.match.port_in) is None:
                GraphError("Flowrule "+flowrule.id+" has not an ingress endpoint ('port_in')")
            
            # Check vlan availability
            if flowrule.match.vlan_id is not None and ResourceDescription().VlanID_isAvailable(int(flowrule.match.vlan_id))==False:
                vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                raise GraphError("Vlan ID "+str(ep.vlan_id)+" not allowed! Valid vlan ids: "+vids_list)
                

            # Detect multiple output actions (they are not allowed).
            # If multiple output are needed, multiple flow rules should be written
            # in the nffg.json, with a different priorities!
            output_action_counter=0
            for a in flowrule.actions:
                if a.controller is not None and a.controller==True:
                    raise_useless_info("presence of 'output_to_controller'")
                if a.output_to_queue is not None:
                    raise_useless_info("presence of 'output_to_queue'")
                if a.output is not None:
                    if output_action_counter > 0:
                        raise_invalid_actions("Multiple 'output_to_port' not allowed (flow rule "+flowrule.id+")")
                    output_action_counter = output_action_counter+1
                    if self.__getEndpointIdFromString(a.output) is None:
                        GraphError("Flowrule "+flowrule.id+" has not an egress endpoint ('output_to_port' in 'action')")
                
                # Check vlan availability
                if a.push_vlan is not None and ResourceDescription().VlanID_isAvailable(int(a.push_vlan))==False:
                    vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                    raise GraphError("Vlan ID "+str(a.push_vlan)+" not allowed! Valid vlan ids: "+vids_list)
                if a.set_vlan_id is not None and ResourceDescription().VlanID_isAvailable(int(a.set_vlan_id))==False:
                    vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                    raise GraphError("Vlan ID "+str(a.set_vlan_id)+" not allowed! Valid vlan ids: "+vids_list)

                
                



    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        OPENDAYLIGHT INTERACTIONS
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
    
    def __NFFG_ODL_deleteGraph(self):
        '''
        Delete a whole graph, and set it as "ended".
        Delete all endpoints, and releated resources.
        Delete all flowrules from database and from opendaylight.
        '''
        
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
        GraphSession().updateEnded(self.__session_id)




    def __NFFG_ODL_DeleteAndUpdate(self, updated_nffg):
        '''
        Remove all endpoints and all flowrules which is marked as 'to_be_deleted'.
        For each flowrule marked as 'already_deployed' this function checks if the
        releated endpoints are been updated: in this case the flowrule is deleted 
        and it is set as 'new' in order that be installed again.   
        '''
        # List of updated endpoints
        updated_endpoints = []
        
        # Delete the endpoints 'to_be_deleted'
        for endpoint in updated_nffg.end_points[:]: # "[:]" keep in memory deleted items during the loop.
            if endpoint.status == 'to_be_deleted':
                self.__deleteEndpointByID(endpoint.db_id)
                updated_nffg.end_points.remove(endpoint)
            elif endpoint.status == 'new' or endpoint.status is None:
                updated_endpoints.append(endpoint.id)
        
        # Delete the flowrules 'to_be_deleted'
        for flowrule in updated_nffg.flow_rules[:]: # "[:]" keep in memory deleted items during the loop.
            
            # Delete flowrule
            if flowrule.status == 'to_be_deleted': #and flowrule.type != 'external':
                self.__deleteFlowRuleByGraphID(flowrule.id)
                updated_nffg.flow_rules.remove(flowrule)
            
            # Set flowrule as "new" when associated endpoint has been updated
            elif flowrule.status == 'already_deployed':
                ep_in = self.__getEndpointIdFromString(flowrule.match.port_in)
                if ep_in is not None and ep_in in updated_endpoints:
                    flowrule.status = 'new'
                else:
                    for a in  flowrule.actions:
                        ep_out = self.__getEndpointIdFromString(a.output)
                        if ep_out is not None and ep_out in updated_endpoints:
                            flowrule.status = 'new'




    def __ProfileGraph_BuildFromNFFG(self, nffg):
        '''
        Create a ProfileGraph with the flowrules and endpoints specified in nffg.
        Return a odl_objects.ProfileGraph object.
        '''
        for endpoint in nffg.end_points:
            
            if endpoint.status is None:
                endpoint.status = "new"
                
            self.NetManager.ProfileGraph.addEndpoint(endpoint)
        
        for flowrule in nffg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            self.NetManager.ProfileGraph.addFlowrule(flowrule)
    
    
    
    
    def __getEndpointIdFromString(self, endpoint_string):
        if endpoint_string is None:
            return None
        endpoint_string = str(endpoint_string)
        tmp2 = endpoint_string.split(':')
        port2_type = tmp2[0]
        port2_id = tmp2[1]
        if port2_type == 'endpoint':
            return port2_id
        return None
    
    
    

    def __ODL_FlowsInstantiation(self, nffg):
        
        # Build the Profile Graph
        self.__ProfileGraph_BuildFromNFFG(nffg)
        
        # [ FLOW RULEs ]
        for flowrule in self.NetManager.ProfileGraph.getFlowrules():
            
            # Check if this flowrule has to be installed
            if flowrule.status !='new':
                continue   
            
            # Get ingress endpoint
            port1_id = self.__getEndpointIdFromString(flowrule.match.port_in)
            in_endpoint = self.NetManager.ProfileGraph.getEndpoint(port1_id)
            
            # Process flow rule with VLAN
            self.__ODL_ProcessFlowrule(in_endpoint, flowrule)
    
    
    
    def __ODL_CheckFlowruleOnEndpoint(self, in_endpoint, flowrule):
        '''
        Check if the flowrule can be installed on the ingress endpoint.
        '''
        
        # Is the endpoint enabled?
        if GraphSession().isDirectEndpoint(in_endpoint.interface, in_endpoint.switch_id):
            raise GraphError("The ingress endpoint "+in_endpoint.id+" is a busy direct endpoind")
        
        # Busy vlan id?
        if GraphSession().ingressVlanIsBusy(flowrule.match.vlan_id, in_endpoint.interface, in_endpoint.switch_id):
            raise GraphError("Flowrule "+flowrule.id+" use a busy vlan id "+flowrule.match.vlan_id+" on the same ingress port (ingress endpoint "+in_endpoint.id+")")
    
    

    def __ODL_ProcessFlowrule(self, in_endpoint, flowrule):
        '''
        in_endpoint = nffg.EndPoint
        flowrule = nffg.FlowRule
        
        Process a flow rule written in the section "big switch" of a nffg json.
        Add a vlan match/mod/strip to every flowrule in order to distinguish it.
        After the verification that output is an endpoint, this function manages
        three main cases:
            1) endpoints are on the same switch;
            2) endpoints are on different switches, so search for a path.
        '''
        
        # Endpoint.type = VLAN ...overwrites the match on vlan_id
        if in_endpoint.type == "vlan":
            flowrule.match.vlan_id = in_endpoint.vlan_id
        
        self.__ODL_CheckFlowruleOnEndpoint(in_endpoint, flowrule)
        
        out_endpoint = None
        
        # Search for a "drop" action.
        # Install immediately the flow rule, and return.
        # If a flow rule has a drop action, we don't care of other actions!
        for a in flowrule.actions:
            if a.drop is True:
                single_efr = OpenDayLightDO.__externalFlowrule( match=Match(flowrule.match), priority=flowrule.priority, flow_id=flowrule.id, nffg_flowrule=flowrule)
                single_efr.setInOut(in_endpoint.switch_id, a, in_endpoint.interface , None, "1")
                self.__Push_externalFlowrule(single_efr)
                return
        
        # Search for the output endpoint
        for a in flowrule.actions:
            if a.output is not None:
                port2_id = self.__getEndpointIdFromString(a.output) # Is the 'output' destination an endpoint?
                if port2_id is not None:
                    out_endpoint = self.NetManager.ProfileGraph.getEndpoint(port2_id) #Endpoint object (declared in resources.py)
                    break
        
        # Out Endpoint not valid
        if out_endpoint is None:
            raise GraphError("Flowrule "+flowrule.id+" has an invalid egress endpoint")

        # [ 1 ] Endpoints are on the same switch
        if in_endpoint.switch_id == out_endpoint.switch_id:
            
            # Error: endpoints are equal!
            if in_endpoint.interface == out_endpoint.interface:
                raise GraphError("Flowrule "+flowrule.id+" is wrong: endpoints are overlapping")
            
            # 'Single-switch' path
            self.__ODL_LinkEndpointsByVlanID([in_endpoint.switch_id], in_endpoint, out_endpoint, flowrule)
            return

        # [ 2 ] Endpoints are on different switches...search for a path!
        nodes_path = self.NetManager.getShortestPath(in_endpoint.switch_id, out_endpoint.switch_id)
        if(nodes_path is not None):
            
            logging.info("Found a path bewteen "+in_endpoint.switch_id+" and "+out_endpoint.switch_id+". "+"Path Length = "+str(len(nodes_path)))
            if self.__ODL_checkEndpointsOnPath(nodes_path, in_endpoint, out_endpoint)==False:
                logging.debug("Invalid link between the endpoints")
                return
            self.__ODL_LinkEndpointsByVlanID(nodes_path, in_endpoint, out_endpoint, flowrule)
            return
            
        # [ 3 ] No paths between the endpoints 
        logging.debug("Cannot find a link between "+in_endpoint.switch_id+" and "+out_endpoint.switch_id)
        return




    def __ODL_checkEndpointsOnPath(self, path, ep1, ep2):
        if len(path)<2:
            return None
        #check if ep1 stays on the link
        if ep1.interface == self.NetManager.switchPortIn(path[0], path[1]):
            logging.debug("...path not valid: endpoint "+ep1.switch_id+" port:"+ep1.interface+" stay on the link!")
            return False
        #check if ep2 stays on the link
        path_last = len(path)-1
        if ep2.interface == self.NetManager.switchPortIn(path[path_last], path[path_last-1]):
            logging.debug("...path not valid: endpoint "+ep2.switch_id+" port:"+ep2.interface+" stay on the link!")
            return False
        return True




    def __ODL_LinkEndpointsByVlanID(self, path, ep1, ep2, flowrule):
        ''' 
        This function links two endpoints with a set of flow rules pushed in
        all the intermediate switches (and in first and last switches, of course).
        
        The link between this endpoints is based on vlan id.
        If no ingress (or egress) vlan id is specified, a suitable vlan id will be chosen.
        In any case, all the vlan ids will be checked in order to avoid possible 
        conflicts in the traversed switches.
        '''

        efr = OpenDayLightDO.__externalFlowrule(flow_id=flowrule.id, priority=flowrule.priority, nffg_flowrule=flowrule)
        
        base_actions = []
        vlan_out = None
        original_vlan_out = None
        vlan_in = None
        pop_vlan_flag = False
        
        # Initialize vlan_id and save it
        if flowrule.match.vlan_id is not None:
            vlan_in = flowrule.match.vlan_id
            original_vlan_out = vlan_in
        
        # Clean actions, search for an egress vlan id and pop vlan action
        for a in flowrule.actions:
            
            # [PUSH VLAN (ID)] Store the VLAN ID and remove the action
            if a.push_vlan is not None:
                vlan_out = a.push_vlan
                original_vlan_out = a.push_vlan
                continue
            
            # [SET VLAN ID] Store the VLAN ID and remove the action
            if a.set_vlan_id is not None:
                vlan_out = a.set_vlan_id
                original_vlan_out = a.set_vlan_id
                continue
            
            # [POP VLAN] Set the flag and remove the action
            if a.pop_vlan is not None and a.pop_vlan==True:
                pop_vlan_flag = True
                continue
            
            # Filter non OUTPUT actions 
            if a.output is None:
                no_output = Action(a)
                base_actions.append(no_output)
        
        ''' Remember to pop vlan header by the last switch.
            If vlan out is not None, a pushvlan/setvlan action is present, and popvlan action is incompatible.
            Otherwise, if vlan in is None, a vlan header will be pushed by the first switch,
            so it will have to be removed by the last switch.
            This flag is also set to True when a "pop-vlan" action and a vlan match are present. 
        '''
        pop_vlan_flag = (vlan_out is None) and (pop_vlan_flag or vlan_in is None)
        
        
        # [PATH] Traverse the path and create the flow for each switch
        for i in range(0, len(path)):
            hop = path[i]
            efr.set_flow_name(i)
            base_match = Match(flowrule.match)
            efr.set_actions(list(base_actions))
            
            # Switch position
            pos = 0 # (-2: 'single-switch' path, -1:first, 0:middle, 1:last)
            
            # Next switch and next ingress port
            next_switch_ID = None
            next_switch_portIn = None
            if i < (len(path)-1):
                next_switch_ID = path[i+1]
                next_switch_portIn = self.NetManager.switchPortIn(next_switch_ID, hop)
            
            # First switch
            if i==0:
                pos = -1
                efr.set_switch_id(ep1.switch_id)
                port_in = ep1.interface
                port_out = self.NetManager.switchPortOut(hop, next_switch_ID)
                if port_out is None and len(path)==1: #'single-switch' path
                    pos = -2
                    port_out = ep2.interface
            
            # Last switch
            elif i==len(path)-1:
                pos = 1
                efr.set_switch_id(ep2.switch_id)
                port_in = self.NetManager.switchPortIn(hop, path[i-1])
                port_out = ep2.interface
                
                # Force the vlan out to be equal to the original
                if pop_vlan_flag == False and original_vlan_out is not None:
                    vlan_out = original_vlan_out
                    
                # Vlan egress endpoint ...set the vlan_id
                if ep2.type=='vlan':
                    pop_vlan_flag = False
                    vlan_out = ep2.vlan_id
            
            # Middle way switch
            else:
                efr.set_switch_id(hop)
                port_in = self.NetManager.switchPortIn(hop, path[i-1])
                port_out = self.NetManager.switchPortOut(hop, next_switch_ID)
            
            # Check, generate and set vlan ids
            vlan_in, vlan_out, set_vlan_out = self.__ODL_VlanTraking(port_in, port_out, vlan_in, vlan_out, next_switch_ID, next_switch_portIn)
            
            # Match
            if vlan_in is not None:
                base_match.setVlanMatch(vlan_in)
                
                # Remove VLAN header
                if pop_vlan_flag and ( pos==1 or pos==-2): #1=last switch; -2='single-switch' path
                    action_stripvlan = Action()
                    action_stripvlan.setPopVlanAction()
                    efr.append_action(action_stripvlan)

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
    
    
    
    
    def __ODL_VlanTraking(self, port_in, port_out, vlan_in=None, vlan_out=None, next_switch_ID=None, next_switch_portIn=None):
        '''
        Receives the main parameters for a "vlan based" flow rule.
        Check all vlan ids on the specified ports of current switch and the next switch.
        If a similar "vlan based" flow rule exists, new vlan in/out will be chosen.
        This function make other some checks to verify the correctness of all parameters.
        
        '''
        # Rectify vlan ids
        if vlan_in is not None:
            vlan_in = int(vlan_in)
            if vlan_in<=0 or vlan_in>=4095:
                vlan_in = None
            elif ResourceDescription().VlanID_isAvailable(vlan_in)==False:
                vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                raise GraphError("Vlan ID "+str(vlan_in)+" not allowed! Valid vlan ids: "+vids_list)
        if vlan_out is not None:
            vlan_out = int(vlan_out)
            if vlan_out<=0 or vlan_out>=4095:
                vlan_out = None
            elif ResourceDescription().VlanID_isAvailable(vlan_out)==False:
                vids_list = str(Configuration().VLAN_AVAILABLE_IDS)
                raise GraphError("Vlan ID "+str(vlan_out)+" not allowed! Valid vlan ids: "+vids_list)
            
        # Detect if a mod_vlan action is needed
        set_vlan_out = None
        if vlan_out is not None and vlan_out != vlan_in:
            set_vlan_out = vlan_out
        
        # Set the output vlan that we have to check in the next switch
        if vlan_in is not None and vlan_out is None:
            vlan_out = vlan_in
        
        # Check if the output vlan can be accepted on next_switch_portIn@next_switch_ID
        if vlan_out is not None and next_switch_ID is not None:
            if GraphSession().ingressVlanIsBusy(vlan_out, next_switch_portIn, next_switch_ID):
                vlan_out = None
        ''' 
            Check if an output vlan id is needed.
            Enter this "if" when vlan_out is None and this happens in two main cases:
                1) when it is not specified;
                2) when it is not compliant with the next switch port in.
        '''
        if vlan_out is None and next_switch_ID is not None:
            vlan_out = self.getFreeIngressVlanID_fromAvailableVlanIDsList(next_switch_portIn,next_switch_ID) #return int or None
            set_vlan_out = vlan_out
        
        return vlan_in, vlan_out, set_vlan_out
    
    
    
    
    def getFreeIngressVlanID_fromAvailableVlanIDsList(self, port_in, switch_id):
        
        # init first available vlan id
        prev_vlan_in = ResourceDescription().VlanID_getFirstAvailableID()
        if prev_vlan_in is None:
            return
        prev_vlan_in = prev_vlan_in-1
        
        # init last available vlan id
        last_vlan_in = ResourceDescription().VlanID_getLastAvailableID()
        if last_vlan_in is None:
            return
        
        # return a free vlan_in [2,4094] for port_in@switch_id
        vlan_ids = GraphSession().getVlanInIDs(port_in, switch_id) #ordered by vlan_id ASC
        
        # Return the smaller vlan id
        if len(vlan_ids)<=0:
            return prev_vlan_in+1
        
        # Search an ingress vlan id suitable for the switch
        for q in vlan_ids:
            if(q.vlan_in is None):
                continue
            this_vlan_in = int(q.vlan_in)
            
            if (this_vlan_in-prev_vlan_in)<2 :
                prev_vlan_in = this_vlan_in
                continue
            
            if ResourceDescription().VlanID_isAvailable(prev_vlan_in+1)==False:
                continue
            
            if (prev_vlan_in+1)>last_vlan_in:
                prev_vlan_in = None
            break
        
        # Latest checks
        if prev_vlan_in is None:
            raise GraphError("All vlan ID are busy on port:"+port_in+" of the "+switch_id)
        
        if prev_vlan_in<1 or prev_vlan_in>=4094:
            raise GraphError("Invalid ingress vlan ID: "+str(prev_vlan_in+1)+" [port:"+port_in+" on "+switch_id+"]")
        
        # Valid VLAN ID
        return (prev_vlan_in+1)


    
    
    
    
    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DATABASE INTERACTIONS
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
    
    def __addVlanTraking(self, efr, flow_rule_db_id):
        # efr = __externalFlowrule
        vlan_in = None
        vlan_out = None
        port_in = None
        port_out = None
        switch_id = efr.get_switch_id()
        
        if(efr.get_match().InputPort is not None):
            port_in = efr.get_match().InputPort
        
        if(efr.get_match().vlan_id is not None):
            vlan_in = efr.get_match().VlanID
            vlan_out = vlan_in
        
        for a in efr.get_actions():
            if(a.is_output_port_action()):
                port_out = a.OutputPort
            if(a.is_set_vlan_action()):
                vlan_out = a.VlanID
            elif(a.is_pop_vlan_action()):
                vlan_out = None
        
        # DATABASE: Add vlan tracking
        GraphSession().addVlanTracking(flow_rule_db_id, switch_id,vlan_in,port_in,vlan_out,port_out)
        
        
    
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
    
    def __deleteFlowRule(self, flow_rule_ref):
        # flow_rule_ref is a FlowRuleModel object
        if flow_rule_ref.type == 'external': #and flow.status == "complete"
            try:
                self.NetManager.deleteFlow(flow_rule_ref.switch_id, flow_rule_ref.internal_id)
            except Exception as ex:
                if type(ex) is HTTPError and ex.response.status_code==404:
                    logging.debug("External flow "+flow_rule_ref.internal_id+" does not exist in the switch "+flow_rule_ref.switch_id+".")
                else:
                    logging.debug("Exception while deleting external flow "+flow_rule_ref.internal_id+" in the switch "+flow_rule_ref.switch_id+". ")
                    raise ex
        GraphSession().deleteFlowruleByID(flow_rule_ref.id)

    def __deletePortByID(self, port_id):
        GraphSession().deletePort(port_id, self.__session_id)
       
    def __deleteEndpointByGraphID(self, graph_endpoint_id):
        ep = GraphSession().getEndpointByGraphID(graph_endpoint_id, self.__session_id)
        if ep is not None:
            self.__deleteEndpointByID(ep.id)

    def __deleteEndpointByID(self, endpoint_id):
        ep_resources = GraphSession().getEndpointResourcesByEndpointID(endpoint_id)
        if ep_resources is None:
            return
        for eprs in ep_resources:
            if eprs.resource_type == 'flow-rule':
                self.__deleteFlowRuleByID(eprs.resource_id)
            elif eprs.resource_type == 'port':
                self.__deletePortByID(eprs.resource_id)
        GraphSession().deleteEndpointByID(endpoint_id)

    
    
    
    
    
    
    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        EXTERNAL FLOWRULE
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''

    def __Push_externalFlowrule(self, efr):
        # efr = __externalFlowrule
        '''
        This is the only function that should be used to push an external flow
        (a "custom flow", in other words) in the database and in the opendaylight controller.
        GraphSession().addFlowrule(...) is also used in GraphSession().updateNFFG 
        and in GraphSession().addNFFG to store the flow rules written in nffg.json.
        '''
        
        '''
        TODO: check if exists a flowrule with the same match criteria in the same switch
            (very rare event); if it exists, raise an exception!
            Similar flow rules are replaced by ovs switch, so one of them disappear!
            def __ODL_ExternalFlowrule_Exists(self, switch, nffg_match, nffg_action).
        '''
        
        # If the flow name already exists, get new one
        self.__checkFlowname_externalFlowrule(efr)

        # ODL/Switch: Add flow rule
        sw_flow_name = self.NetManager.createFlow(efr) #efr.get_flow_name()
        
        # DATABASE: Add flow rule
        flow_rule = NffgFlowrule(_id=efr.get_flow_id(),node_id=efr.get_switch_id(), _type='external', status='complete',
                                 priority=efr.get_priority(), internal_id=sw_flow_name)
        flow_rule_db_id = GraphSession().addFlowrule(self.__session_id, efr.get_switch_id(), flow_rule)
        GraphSession().dbStoreMatch(efr.getNffgMatch(), flow_rule_db_id, flow_rule_db_id)
        GraphSession().dbStoreAction(efr.getNffgAction(), flow_rule_db_id)
        
        # DATABASE: Add vlan tracking
        self.__addVlanTraking(efr, flow_rule_db_id)
    
    
    
    def __checkFlowname_externalFlowrule(self, efr):
        '''
        Check if the flow name already exists on the same switch,
        in order to avoid subscribing the existing flowrule in one switch.
        '''
        if GraphSession().externalFlowruleExists(efr.get_switch_id(),efr.get_flow_name())==False:
            return
        
        efr.set_flow_name(0)
        this_efr = OpenDayLightDO.__externalFlowrule()
        
        flow_rules_ref = GraphSession().getExternalFlowrulesByGraphFlowruleID(efr.get_switch_id(),efr.get_flow_id())
        for fr in flow_rules_ref:
            if fr.type != 'external' or fr.internal_id is None:
                continue
            
            this_efr.set_complete_flow_name(fr.internal_id)
            
            if this_efr.compare_flow_name(efr.get_flow_name())<2: #[ ( this_efr.flow_name - prev_efr.flow_name ) < 2 ]
                efr.set_complete_flow_name(fr.internal_id)
                continue            
            break
        efr.inc_flow_name()
            
            
        
        
        
    
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
            
            # match = odl_resources.Match object
            self.__match = match
            
            # actions = array of odl_resources.Action object
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
            self.__flow_name_suffix = None
            if(suffix is not None and str(suffix).isdigit()):
                self.__flow_name = self.__flow_name + str(suffix)
                self.__flow_name_suffix = int(suffix)
        
        def set_complete_flow_name(self, flow_name):
            fn = self.split_flow_name(flow_name)
            if len(fn)<2:
                return
            self.__flow_id = fn[0]
            self.set_flow_name(fn[1])

        def set_priority(self, value):
            self.__priority = value
        
        def split_flow_name(self, flow_name=None):
            if flow_name is not None:
                fn = flow_name.split("_")
                if len(fn)<2:
                    return None
                if fn[1].isdigit()==False:
                    return None
                fn[1]=int(fn[1])
                return fn
            return [self.__flow_id,self.__flow_name_suffix]
        
        def inc_flow_name(self):
            fn = self.split_flow_name()
            if fn is not None:
                self.set_flow_name(int(fn[1])+1)
        
        def compare_flow_name(self, flow_name):
            fn1 = self.split_flow_name()
            if fn1 is None:
                return 0
            fn2 = self.split_flow_name(flow_name)
            if fn2 is None:
                return 0
            fn1[1] = int(fn1[1])
            fn2[1] = int(fn2[1])
            return ( fn1[1] - fn2[1] )
            
            

        def setInOut(self, switch_id, action, port_in, port_out, flowname_suffix):
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
            return self.__match.getNffgMatch(self.__nffg_flowrule)
            

        def getNffgAction(self):
            base_action = Action()
            return base_action.getNffgAction(self.__actions, self.__nffg_flowrule)

