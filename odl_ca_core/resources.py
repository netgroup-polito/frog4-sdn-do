'''
Created on 13/mag/2015

@author: vida
@author: giacomoratta
'''

import json
import logging

'''
######################################################################################################
########################       Classes which represent ODL objects        ############################
######################################################################################################
'''

class Flow(object):
    def __init__(self, name, flow_id, table_id = 0, priority = 5, installHw = True, 
                 hard_timeout = 0, idle_timeout = 0, actions = None, match = None):
        '''
        Constructor for the Flow
        Args:
            name:
                flow name (not really useful)
            flow_id:
                identifier of the flow (to be recorded for further deletion)
            table_id:
                identifier of the table where to install the flow (in OF1.0 can be only table0!!)
            priority:
                flow priority
            installHw:
                boolean to force installation on the switch (default = True)
            hard_timeout:
                time before flow deletion (default = 0 = no timeout)
            idle_timeout:
                inactivity time before flow deletion (default = 0 = no timeout)
            actions:
                list of Actions for this flow
            match:
                Match for this flow
        '''
        self.strict = False
        self.name = name
        self.flow_id = flow_id
        self.table_id = table_id
        self.priority = priority
        self.installHw = installHw
        self.hard_timeout = hard_timeout
        self.idle_timeout = idle_timeout
        
        self.actions = actions or []
        self.match = match
    
    def getJSON(self, odl_version, node = None):
        '''
        Gets the JSON. In Hydrogen returns the JSON associated to the given node
        Args:
            node:
                The id of the node related to this JSON (only Hydrogen)
        '''
        j_flow = {}
        j_list_action = []
        
        #Sort actions
        self.actions.sort(key=lambda x: x.priority)
        
        if odl_version == "Hydrogen":
            j_flow['name'] = self.flow_id
            j_flow['node'] = {}
            j_flow['node']['id']= node
            j_flow['node']['type']="OF"
            j_flow['priority'] = self.priority
            j_flow['installInHw'] = self.installHw
            j_flow['hardTimeout'] = self.hard_timeout
            j_flow['idleTimeout'] = self.idle_timeout

            if (self.match.input_port is not None):
                j_flow['ingressPort'] = self.match.input_port                                    
            if (self.match.ip_source is not None):
                j_flow['nwSrc'] = self.match.ip_source
            if (self.match.ip_dest is not None):
                j_flow['nwDst'] = self.match.ip_dest
            if (self.match.vlan_id is not None):
                j_flow['vlanId'] = self.match.vlan_id
            if (self.match.ethertype is not None):
                j_flow['etherType'] = self.match.ethertype
            if (self.match.eth_source is not None):
                j_flow['dlSrc'] = self.match.eth_source
            if (self.match.eth_dest is not None):
                j_flow['dlDst'] = self.match.eth_dest
            if (self.match.ip_protocol is not None):
                j_flow['protocol'] = self.match.ip_protocol               
                
            if (self.match.port_source is not None):
                if (self.match.ip_protocol is not None and self.match.ethertype is not None):
                    j_flow['tpSrc'] = self.match.port_source
                else:
                    logging.warning('sourcePort discarded. You have to set also "protocol" and "ethertype" fields')
                    
            if (self.match.port_dest is not None):
                if (self.match.ip_protocol is not None and self.match.ethertype is not None):
                    j_flow['tpDst'] = self.match.port_dest
                else:
                    logging.warning('destPort discarded. You have to set also "protocol" and "ethertype" fields')                    
            """        
            if self.match.tp_match is True and self.match.ethertype is None:
                j_flow['etherType'] = "0x800"
                logging.warning("Hydrogen requires ethertype set in order to perform transport protocol match: ethertype has been set to 0x800")

                
            if self.match.tp_match is True and self.match.protocol is None:
                proto = self.match.port_source.split(":")[0]
                j_flow['protocol'] = proto
                logging.warning("Hydrogen requires protocol set in order to perform transport protocol match: protocol has been set to "+proto)
            """
                       
            if (self.match.ip_match is True and self.match.ethertype is None):
                j_flow['etherType'] = "0x800"
                logging.warning("Hydrogen requires ethertype set in order to perform ip match: ethertype has been set to 0x800")
            
            for action in self.actions:
                
                # it seems to be useless for Hydrogen 
                #if action.action_type == "vlan-match":
                #    j_action = unicode("PUSH_VLAN")
                #    j_list_action.append(j_action)
                
                j_action = action.getActionsHydrogen()    
                j_list_action.append(j_action)
                
            j_flow['actions'] = j_list_action;

        else:
            j_flow['flow'] = {}
            j_flow['flow']['strict'] = self.strict
            j_flow['flow']['flow-name'] = self.name
            j_flow['flow']['id'] = self.flow_id
            j_flow['flow']['table_id'] = self.table_id
            j_flow['flow']['priority'] = self.priority
            j_flow['flow']['installHw'] = self.installHw
            j_flow['flow']['hard-timeout'] = self.hard_timeout
            j_flow['flow']['idle-timeout'] = self.idle_timeout
            
            j_flow['flow']['instructions'] = {}
            j_flow['flow']['instructions']['instruction'] = {}
            j_flow['flow']['instructions']['instruction']['order'] = str(0)
            j_flow['flow']['instructions']['instruction']['apply-actions'] = {}
            
            i = 0
            for action in self.actions:
                
                j_action = {}
                
                # required to tag a frame without vlan header 
                #if action.action_type == "vlan-match":
                #    j_action['order'] = i
                #    j_action['push-vlan-action'] = {}
                #    j_action['push-vlan-action']['ethernet-type'] = 33024
                #    j_list_action.append(j_action)
                #    i = i + 1
                
                j_action = action.getActions(i)
                j_list_action.append(j_action)
                i = i + 1
            
            j_flow['flow']['instructions']['instruction']['apply-actions']['action'] = j_list_action
            

            if (self.match is not None):
                j_flow['flow']['match'] = {}
                
                if (self.match.input_port is not None):
                    j_flow['flow']['match']['in-port'] = self.match.input_port
                if (self.match.ip_source is not None):
                    j_flow['flow']['match']['ipv4-source'] = self.match.ip_source
                if (self.match.ip_dest is not None):
                    j_flow['flow']['match']['ipv4-destination'] = self.match.ip_dest
                if (self.match.ip_protocol is not None):
                    j_flow['flow']['match']['ip-match'] = {}
                    j_flow['flow']['match']['ip-match']['ip-protocol'] = self.match.ip_protocol
 
                if (self.match.port_source is not None):
                    if (self.match.ip_protocol is not None):
                        protocol = self.match.ip_protocol
                        if protocol == "6":
                            protocol = "tcp"
                        elif protocol == "17":
                            protocol = "udp"
                        j_flow['flow']['match'][protocol+'-source-port'] = self.match.port_source
                    else:
                        logging.warning('sourcePort discarded. You have to set also the "protocol" field')

                if (self.match.port_dest is not None):
                    if (self.match.ip_protocol is not None):
                        protocol = self.match.ip_protocol
                        if protocol == "6":
                            protocol = "tcp"
                        elif protocol == "17":
                            protocol = "udp"
                        j_flow['flow']['match'][protocol+'-destination-port'] = self.match.port_dest
                    else:
                        logging.warning('destPort discarded. You have to set also the "protocol" field')
                        
                if (self.match.vlan_id is not None):
                    j_flow['flow']['match']['vlan-match'] = {}
                    j_flow['flow']['match']['vlan-match']['vlan-id'] = {}
                    j_flow['flow']['match']['vlan-match']['vlan-id']['vlan-id'] = self.match.vlan_id
                    j_flow['flow']['match']['vlan-match']['vlan-id']['vlan-id-present'] = self.match.vlan_id_present
                if (self.match.eth_match is True):
                    j_flow['flow']['match']['ethernet-match'] = {}
                    if (self.match.ethertype is not None):
                        j_flow['flow']['match']['ethernet-match']['ethernet-type'] = {}
                        j_flow['flow']['match']['ethernet-match']['ethernet-type']['type'] = self.match.ethertype
                    if (self.match.eth_source is not None):
                        j_flow['flow']['match']['ethernet-match']['ethernet-source'] = {}
                        j_flow['flow']['match']['ethernet-match']['ethernet-source']['address'] = self.match.eth_source
                    if (self.match.eth_dest is not None):
                        j_flow['flow']['match']['ethernet-match']['ethernet-destination'] = {}
                        j_flow['flow']['match']['ethernet-match']['ethernet-destination']['address'] = self.match.eth_dest
        
        return json.dumps(j_flow)

class Action(object):
    def __init__(self, action = None):
        '''
        Represents any OpenFlow 1.0 possible action on the outgoing traffic
        '''
        self.address = None
        self.action_type = None
        self.output_port = None
        self.max_length = None
        self.vlan_id = None
        self.vlan_id_present = False
        self.priority = 0 # priority used to sort actions list
        if action is not None:
            #TODO: add remaining actions
            if action.drop is True:
                self.setDropAction()
            elif action.controller is True:
                self.setControllerAction()
            elif action.set_vlan_id is not None:
                self.setSwapVlanAction(action.set_vlan_id)
            elif action.pop_vlan is True:
                self.setPopVlanAction()
            elif action.set_ethernet_src_address is not None:
                self.setEthernetAddressAction("source", action.set_ethernet_src_address)
            elif action.set_ethernet_dst_address is not None:
                self.setEthernetAddressAction("destination", action.set_ethernet_dst_address)                

    def setEthernetAddressAction(self, _type, address):
        self.priority = 4
        self.address = address
        if _type=="source":
            self.action_type = "set-dl-src-action"
        elif _type=="destination":
            self.action_type = "set-dl-dst-action"

    def setDropAction(self):
        self.action_type = "drop-action"
        
    def setPopVlanAction(self):
        self.action_type="pop-vlan-action"
        self.priority = 2
    
    def setPushVlanAction(self):
        self.action_type="push-vlan-action"
        self.priority = 2
        
    def setControllerAction(self):
        self.action_type = "output-action"
        self.output_port = "CONTROLLER"
        self.max_length = 65535
        self.priority = 9
    
    def setOutputAction(self, out_port, max_length):
        '''
        Define this action as an output port action
        Args:
            out_port:
                id of the output port where to send out the traffic
            max_lenght:
                max length of the packets
        '''
        self.action_type = "output-action"
        self.output_port = out_port
        self.max_length = max_length
        self.priority = 10
    
    def setSwapVlanAction(self, vlan_id):
        '''
        Define this action as a vlan tag swapping action
        Args:
            vlan_id:
                vlan id for the new tag
        '''
        self.action_type = "vlan-match"
        self.vlan_id = vlan_id
        self.vlan_id_present = True
        self.priority = 8
        
    def getActionsHydrogen(self):
        '''
        Returns actions formatted for Hydrogen
        '''
        j_action = None
        if self.action_type == "set-dl-src-action":
            j_action = "SET_DL_SRC="+self.address
        elif self.action_type == "set-dl-dst-action":
            j_action = "SET_DL_DST="+self.address
        elif self.action_type == "push-vlan-action":
            j_action = "PUSH_VLAN"
        elif self.action_type == "pop-vlan-action":
            j_action = "POP_VLAN"
        elif self.action_type == "drop-action":
            j_action = "DROP"
        elif self.action_type == "output-action":
            if self.output_port == "CONTROLLER":
                j_action = "CONTROLLER"
            else:
                j_action = "OUTPUT="+self.output_port
        elif self.action_type == "vlan-match":
            j_action = "SET_VLAN_ID="+self.vlan_id
        return j_action
    
    def getActions(self, order):
        '''
        Gets the Action as an object (to be inserted in Flow actions list)
        Args:
            order:
                the order number of this action in the Flow list
        '''
        j_action = {}
        j_action['order'] = order
        
        if self.action_type == "set-dl-src-action":
            j_action['set-dl-src-action'] = {}
            j_action['set-dl-src-action']['address'] = self.address
        elif self.action_type == "set-dl-dst-action":
            j_action['set-dl-dst-action'] = {}
            j_action['set-dl-dst-action']['address'] = self.address
        elif self.action_type == "push-vlan-action":
            j_action['push-vlan-action'] = {}
            j_action['push-vlan-action']['ethernet-type'] = 33024
        elif self.action_type == "pop-vlan-action":
            j_action['pop-vlan-action'] = {}
        elif self.action_type == "drop-action":
            j_action['drop-action'] = {}
        elif self.action_type == "output-action":
            j_action['output-action'] = {}
            j_action['output-action']['output-node-connector'] = self.output_port
            j_action['output-action']['max-length'] = self.max_length
        elif self.action_type == "vlan-match":
            j_action['set-field'] = {}
            j_action['set-field']['vlan-match'] = {}
            j_action['set-field']['vlan-match']['vlan-id'] = {}
            j_action['set-field']['vlan-match']['vlan-id']['vlan-id'] = self.vlan_id
            j_action['set-field']['vlan-match']['vlan-id']['vlan-id-present'] = self.vlan_id_present
        
        return j_action
    
class Match(object):
    def __init__(self, match = None):
        '''
        Represents any OpenFlow 1.0 possible matching rules for the incoming traffic
        '''
        self.input_port = None
        self.vlan_id = None
        self.vlan_id_present = None
        self.eth_match = False
        self.ethertype = None
        self.eth_source = None
        self.eth_dest = None
        self.ip_protocol = None
        self.ip_match = None
        self.ip_source = None
        self.ip_dest = None
        self.tp_match = None
        self.port_source = None
        self.port_dest = None
        if match is not None:
            if match.vlan_id is not None:
                self.setVlanMatch(match.vlan_id)
            #if match.vlan_priority is not None:
                #self.VlanPriority(match.vlan_priority)
            if match.ether_type is not None:
                self.setEtherTypeMatch(match.ether_type)
            if match.source_mac is not None or match.dest_mac is not None:
                self.setEthernetMatch(match.source_mac, match.dest_mac)
            if match.source_ip is not None or match.dest_ip is not None:
                self.setIPMatch(match.source_ip, match.dest_ip)
            if match.protocol is not None:
                self.setIPProtocol(match.protocol)
            if match.source_port is not None or match.dest_port is not None:
                self.setTpMatch(match.source_port, match.dest_port)                
                
                #Tos Bits
        
    def setInputMatch(self, in_port):
        '''
        Define this Match as an input port matching
        Args:
            in_port:
                the input port identifier
        '''
        self.input_port = in_port
    
    def setVlanMatch(self, vlan_id):
        '''
        Define this Match as an input port matching
        Args:
            vlan_id:
                the vlan identifier
        '''
        self.vlan_id = vlan_id
        self.vlan_id_present = True
        
    def setEtherTypeMatch(self, ethertype):
        self.eth_match = True
        self.ethertype = ethertype
        
    def setEthernetMatch(self, eth_source = None, eth_dest = None):
        self.eth_match = True
        self.eth_source = eth_source
        self.eth_dest = eth_dest
        
    def setIPProtocol(self, protocol):
        self.ip_protocol = protocol
        
    def setIPMatch(self, ip_source = None, ip_dest = None):
        self.ip_match = True
        self.ip_source = ip_source
        self.ip_dest = ip_dest
        
    def setTpMatch(self, port_source = None, port_dest = None):
        '''
        Sets a transport protocol match
        '''
        self.tp_match = True
        self.port_source = port_source
        self.port_dest = port_dest
    
'''
######################################################################################################
#####################       Classes which represent resources into graphs       ######################
######################################################################################################
'''

class Endpoint(object):
    def __init__(self, end_id, name, end_type, vlan_id, switch_id, interface, status, remote_graph = None, remote_id = None):
        self.id = end_id
        self.name = name
        self.type = end_type
        self.vlan_id = vlan_id
        self.switch_id = switch_id
        self.interface = interface
        self.status = status
        self.remote_graph = remote_graph
        self.remote_id = remote_id
    
class ProfileGraph(object):
    def __init__(self):
        '''
        Stores the profile graph of the user
        '''
        self._id = None
        self.endpoints = {}
        self.flowrules = {}
    
    # TODO: rename id in session_id, for clarity
    
    @property
    def id(self):
        return self._id
    
    def setId(self, profile_id):
        '''
        Set profile id
        '''
        self._id = profile_id
    
    def addEndpoint(self, endpoint):
        '''
        Add a new endpoint to the graph
        '''
        self.endpoints[endpoint.id] = endpoint
        
    def addFlowrule(self, flowrule):
        self.flowrules[flowrule.id] = flowrule
        