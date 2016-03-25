'''
Created on 13/mag/2015

@author: vida
@author: giacomoratta
'''

import json
from do_core.controller_interface.objects import Flow_Interface, Action_Interface, Match_Interface, NffgAction, NffgMatch


class Flow(Flow_Interface):
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
    
    
    def getJSON_Hydrogen(self, node):
        
        j_flow = {}        
        j_flow['name'] = self.flow_id
        j_flow['node'] = {}
        j_flow['node']['id']= node
        j_flow['node']['type']="OF"
        j_flow['priority'] = self.priority
        j_flow['installInHw'] = self.installHw
        j_flow['hardTimeout'] = self.hard_timeout
        j_flow['idleTimeout'] = self.idle_timeout
        
        # ACTIONS
        j_flow['actions'] = []
        for a in self.actions:                
            j_flow['actions'].append(a.getAction_Hydrogen())

        # MATCH
        if (self.match.input_port is not None):
            j_flow['ingressPort'] = self.match.input_port
        if (self.match.vlan_id is not None):
            j_flow['vlanId'] = self.match.vlan_id
        if (self.match.ethertype is not None):
            j_flow['etherType'] = self.match.ethertype
        if (self.match.eth_source is not None):
            j_flow['dlSrc'] = self.match.eth_source
        if (self.match.eth_dest is not None):
            j_flow['dlDst'] = self.match.eth_dest
        
        return json.dumps(j_flow)
        
        '''                                    
        if (self.match.ip_source is not None):
            j_flow['nwSrc'] = self.match.ip_source
        if (self.match.ip_dest is not None):
            j_flow['nwDst'] = self.match.ip_dest
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
                
        if self.match.tp_match is True and self.match.ethertype is None:
            j_flow['etherType'] = "0x800"
            logging.warning("Hydrogen requires ethertype set in order to perform transport protocol match: ethertype has been set to 0x800")
        if self.match.tp_match is True and self.match.protocol is None:
            proto = self.match.port_source.split(":")[0]
            j_flow['protocol'] = proto
            logging.warning("Hydrogen requires protocol set in order to perform transport protocol match: protocol has been set to "+proto)
            
        if (self.match.ip_match is True and self.match.ethertype is None):
            j_flow['etherType'] = "0x800"
            logging.warning("Hydrogen requires ethertype set in order to perform ip match: ethertype has been set to 0x800")
        '''
        
        
    def getJSON_HeliumLithium(self):
        
        j_flow = {}
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
        j_list_action = []
        for action in self.actions:
            
            j_action = {}
            j_action = action.getAction_HeliumLithium(i)
            j_list_action.append(j_action)
            i = i + 1
        
        j_flow['flow']['instructions']['instruction']['apply-actions']['action'] = j_list_action
        
        
        if self.match is not None:
            j_flow['flow']['match'] = {}
            
            if (self.match.input_port is not None):
                j_flow['flow']['match']['in-port'] = self.match.input_port
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
                '''
                if (self.match.eth_source is not None):
                    j_flow['flow']['match']['ethernet-match']['ethernet-source'] = {}
                    j_flow['flow']['match']['ethernet-match']['ethernet-source']['address'] = self.match.eth_source
                if (self.match.eth_dest is not None):
                    j_flow['flow']['match']['ethernet-match']['ethernet-destination'] = {}
                    j_flow['flow']['match']['ethernet-match']['ethernet-destination']['address'] = self.match.eth_dest
                '''            
            '''
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
            '''
        return json.dumps(j_flow)
        

    
    def getJSON(self, odl_version, node=None):
        '''
        Gets the JSON. In Hydrogen returns the JSON associated to the given node
        Args:
            node:
                The id of the node related to this JSON (only Hydrogen)
        '''
        
        #Sort actions
        self.actions.sort(key=lambda x: x.priority)
        
        if odl_version == "Hydrogen":
            return self.getJSON_Hydrogen(node)

        return self.getJSON_HeliumLithium()
    
            






class Action(Action_Interface):
    def __init__(self, action = None):
        '''
        Represents any OpenFlow 1.0 possible action on the outgoing traffic
        '''
        self.priority = 0 # priority used to sort actions list      
        
        self.action_type = None
        self.output_port = None
        self.max_length = None
        self.vlan_id = None
        self.vlan_id_present = False
        
        if action is not None:
            #TODO: add remaining actions
            if action.drop is True:
                self.setDropAction()
            elif action.controller is True:
                self.setControllerAction()
            elif action.set_vlan_id is not None:
                self.setSwapVlanAction(action.set_vlan_id)
            elif action.push_vlan is not None:
                self.setPushVlanAction()
            elif action.pop_vlan is True:
                self.setPopVlanAction()
            elif action.output is not None:
                self.setOutputAction(action.output,65535)

    
    @property
    def OutputPort(self):
        return self.output_port
    
    @property
    def VlanID(self):
        return self.vlan_id
    
    
    def setControllerAction(self):
        self.action_type = "output-action"
        self.output_port = "CONTROLLER"
        self.max_length = 65535
        self.priority = 9
        
    
    def setOutputAction(self, out_port, max_length):
        self.action_type = "output-action"
        self.output_port = out_port
        self.max_length = max_length
        self.priority = 10
    
    
    def setDropAction(self):
        self.action_type = "drop-action"
        
    
    def setPushVlanAction(self):
        self.action_type="push-vlan-action"
        self.priority = 2


    def setSwapVlanAction(self, vlan_id):
        self.action_type = "vlan-match"
        self.vlan_id = vlan_id
        self.vlan_id_present = True
        self.priority = 8


    def setPopVlanAction(self):
        self.action_type="pop-vlan-action"
        self.priority = 2
    
    '''
    def setEthernetAddressAction(self, _type, address):
        self.priority = 4
        self.address = address
        if _type=="source":
            self.action_type = "set-dl-src-action"
        elif _type=="destination":
            self.action_type = "set-dl-dst-action"
    '''


    def getNffgAction(self, actions, nffg_flowrule):
        # actions = [] , list
        
        output_to_port = None
        output_to_controller = False
        drop = False
        set_vlan_id = None
        push_vlan = None
        pop_vlan = False
        
        # Not supported fields
        set_ethernet_src_address = None
        set_ethernet_dst_address = None
        set_vlan_priority = None
        set_ip_src_address = None 
        set_ip_dst_address= None
        set_ip_tos = None
        set_l4_src_port=None
        set_l4_dst_port = None
        output_to_queue= None
        db_id = None
        
        # Compress all actions in a single NffgAction (for dbStoreAction)
        # Multiple output not allowed
        for a in actions:
            if a.is_output_port_action():
                output_to_port = a.output_port
            elif a.is_output_controller_action():
                output_to_controller = True
            elif a.is_drop_action():
                drop = True
            elif a.is_set_vlan_action():
                set_vlan_id = a.vlan_id
                if push_vlan is not None:
                    push_vlan = set_vlan_id
            elif a.is_push_vlan_action():
                push_vlan = -1
                if set_vlan_id is not None:
                    push_vlan = set_vlan_id
            elif a.is_pop_vlan_action():
                pop_vlan = True

        return NffgAction(output = output_to_port, controller = output_to_controller, drop = drop, 
                          set_vlan_id = set_vlan_id, set_vlan_priority = set_vlan_priority, push_vlan = push_vlan, pop_vlan = pop_vlan,
                          set_ethernet_src_address = set_ethernet_src_address, set_ethernet_dst_address= set_ethernet_dst_address,
                          set_ip_src_address = set_ip_src_address, set_ip_dst_address = set_ip_dst_address,
                          set_ip_tos = set_ip_tos, set_l4_src_port = set_l4_src_port, set_l4_dst_port = set_l4_dst_port, 
                          output_to_queue = output_to_queue, db_id = db_id)
    
    
        
    def getAction_Hydrogen(self):
        '''
        Returns actions formatted for Hydrogen
        '''
        j_action = None
        if self.action_type == "push-vlan-action":
            j_action = "PUSH_VLAN"
        elif self.action_type == "pop-vlan-action":
            j_action = "POP_VLAN"
        elif self.action_type == "drop-action":
            j_action = "DROP"
        elif self.action_type == "output-action":
            if self.output_port == "CONTROLLER":
                j_action = "CONTROLLER"
            else:
                j_action = "OUTPUT="+str(self.output_port)
        elif self.action_type == "vlan-match":
            j_action = "SET_VLAN_ID="+str(self.vlan_id)

        '''
        elif self.action_type == "set-dl-src-action":
            j_action = "SET_DL_SRC="+str(self.address)
        elif self.action_type == "set-dl-dst-action":
            j_action = "SET_DL_DST="+str(self.address)
        '''
        return j_action



    def getAction_HeliumLithium(self, order):
        '''
        Gets the Action as an object (to be inserted in Flow actions list)
        Args:
            order:
                the order number of this action in the Flow list
        '''
        j_action = {}
        j_action['order'] = order
        
        if self.action_type == "push-vlan-action":
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
        
        '''
        elif self.action_type == "set-dl-src-action":
            j_action['set-dl-src-action'] = {}
            j_action['set-dl-src-action']['address'] = self.address
        elif self.action_type == "set-dl-dst-action":
            j_action['set-dl-dst-action'] = {}
            j_action['set-dl-dst-action']['address'] = self.address
        '''
        return j_action
    
    
    def is_push_vlan_action(self):
        return self.action_type == "push-vlan-action"
    
    def is_pop_vlan_action(self):
        return self.action_type == "pop-vlan-action"
    
    def is_drop_action(self):
        return self.action_type == "drop-action"
    
    def is_output_port_action(self):
        return (self.action_type == "output-action" and self.output_port.isdigit())
    
    def is_output_controller_action(self):
        return (self.action_type == "output-action" and self.output_port=="CONTROLLER")
    
    def is_set_vlan_action(self):
        return self.action_type == "vlan-match"
    
    '''
    def is_eth_src_action(self):
        return self.action_type == "set-dl-src-action"
    
    def is_eth_dst_action(self):
        return self.action_type == "set-dl-dst-action"
    
    '''




class Match(Match_Interface):
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
        
        '''
        self.ip_protocol = None
        self.ip_match = None
        self.ip_source = None
        self.ip_dest = None
        self.tp_match = None
        self.port_source = None
        self.port_dest = None
        '''
        
        if match is not None:
            #TODO: add remaining match
            if match.port_in is not None:
                self.setInputMatch(match.port_in)
            if match.vlan_id is not None:
                self.setVlanMatch(match.vlan_id)
            if match.ether_type is not None:
                self.setEtherTypeMatch(match.ether_type)
            if match.source_mac is not None:
                self.setEtherSource(match.source_mac)
            if match.dest_mac is not None:
                self.setEtherDest(match.dest_mac)

        
    def setInputMatch(self, in_port):
        self.input_port = in_port
    
    def setVlanMatch(self, vlan_id):
        self.vlan_id = vlan_id
        self.vlan_id_present = True
        
    def setEtherTypeMatch(self, ethertype):
        self.eth_match = True
        self.ethertype = ethertype
        
    def setEtherSource(self, eth_source):
        self.eth_match = True
        self.eth_source = eth_source
    
    def setEtherDest(self, eth_dest):
        self.eth_match = True
        self.eth_dest = eth_dest
    
    @property
    def InputPort(self):
        return self.input_port
    
    @property
    def VlanID(self):
        return self.vlan_id
    
    @property
    def EtherSource(self):
        return self.eth_source
    
    @property
    def EtherDest(self):
        return self.eth_dest
    
    
    
    def getNffgMatch(self, nffg_flowrule):
        
        port_in = self.input_port
        ether_type = self.ethertype
        vlan_id = self.vlan_id
        source_mac = self.eth_source
        dest_mac = self.eth_dest
        
        # Not supported
        source_ip = None
        dest_ip = None
        source_port = None
        dest_port = None
        protocol = None
        
        # Not directly supported fields
        tos_bits = nffg_flowrule.match.tos_bits
        vlan_priority = nffg_flowrule.match.vlan_priority
        db_id = None
        
        return NffgMatch(port_in=port_in, ether_type=ether_type, 
                         vlan_id=vlan_id, vlan_priority=vlan_priority,
                         source_mac=source_mac, dest_mac=dest_mac, 
                         source_ip=source_ip, dest_ip=dest_ip, 
                         tos_bits=tos_bits,
                         source_port=source_port, dest_port=dest_port,
                         protocol=protocol, db_id=db_id)

    '''        
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
        #Sets a transport protocol match
        self.tp_match = True
        self.port_source = port_source
        self.port_dest = port_dest
    '''
