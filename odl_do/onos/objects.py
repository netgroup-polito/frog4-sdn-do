'''
Created on 2/feb/2016

@author: giacomoratta
'''

import json
from odl_do.controller_interface.objects import Flow_Interface, Action_Interface, Match_Interface, NffgAction, NffgMatch



class Flow(Flow_Interface):
    def __init__(self, deviceId, priority=100, isPermanent=True, timeout=0, treatments=None, selector=None):
        
        self.deviceId = deviceId
        self.priority = priority
        self.isPermanent = isPermanent
        self.timeout = timeout
        
        self.treatments = treatments or []
        self.selector = selector
    
    def getJSON(self):
        j_flow = {}
        
        #Sort actions
        self.treatments.sort(key=lambda x: x.priority)
        
        j_flow['deviceId'] = self.deviceId
        j_flow['priority'] = self.priority
        j_flow['isPermanent'] = self.isPermanent
        j_flow['timeout'] = self.timeout
        
        j_flow['treatment'] = {}
        j_flow['selector'] = {}
        
        j_flow['selector']['criteria'] = self.selector.getCriteria()
        if j_flow['selector']['criteria']==None:
            j_flow['selector']['criteria']=[]
        
        i = 0
        j_treatments = []
        for treatment in self.treatments:
            
            j_treatment = {}
            j_treatment = treatment.getInstruction(i)
            j_treatments.append(j_treatment)
            i = i + 1
        
        j_flow['treatment']['instructions'] = j_treatments
        
        return json.dumps(j_flow)




class Treatment(Action_Interface):
    def __init__(self, action = None):
        '''
        Represents any OpenFlow 1.0 possible action on the outgoing traffic
        Args:
            action:
                an action object from the nffg_library package
        '''
        self.priority = 0 # priority used to sort actions list
        self.json_instr = None
        
        self.type = None
        self.subtype = None
        
        self.port = None
        self.output_port = None
        self.vlanId = None
        
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
    
    
    @property
    def OutputPort(self):
        return self.output_port
    
    @property
    def VlanID(self):
        return self.vlanId
    
    
    def setControllerAction(self, max_length):
        self.type = 'OUTPUT'
        self.subtype = None
        self.port = 'CONTROLLER'
        self.priority = 9
        
        self.json_instr = {}
        self.json_instr['type'] = self.type
        self.json_instr['port'] = self.port
    
    
    def setOutputAction(self, out_port, max_length):
        self.type = 'OUTPUT'
        self.subtype = None
        self.port = out_port
        self.output_port = out_port
        self.priority = 10
        
        self.json_instr = {}
        self.json_instr['type'] = self.type
        self.json_instr['port'] = self.output_port
    
    
    def setDropAction(self):
        self.type = 'NOACTION'
        self.subtype = None
        
        self.json_instr = {}
        self.json_instr['type'] = self.type
        

    def setPushVlanAction(self):
        self.type = 'L2MODIFICATION'
        self.subtype = 'VLAN_PUSH'
        self.priority = 2
        
        self.json_instr = {}
        self.json_instr['type'] = self.type
        self.json_instr['subtype'] = self.subtype
        
        
    def setSwapVlanAction(self, vlan_id):
        self.type='L2MODIFICATION'
        self.subtype = 'VLAN_ID'
        self.vlanId = vlan_id
        self.priority = 8
        
        self.json_instr = {}
        self.json_instr['type'] = self.type
        self.json_instr['subtype'] = self.subtype
        self.json_instr['vlanId'] = self.vlanId
        
    
    def setPopVlanAction(self):
        self.type='L2MODIFICATION'
        self.subtype = 'VLAN_POP'
        self.priority = 2
        
        self.json_instr = {}
        self.json_instr['type'] = self.type
        self.json_instr['subtype'] = self.subtype
    
    
    def is_push_vlan_action(self):
        return self.subtype == "VLAN_PUSH"
    
    def is_set_vlan_action(self):
        return self.subtype == "VLAN_ID"
    
    def is_pop_vlan_action(self):
        return self.subtype == "VLAN_POP"
    
    def is_drop_action(self):
        return self.type == "NOACTION"
    
    def is_output_port_action(self):
        return (self.type == "OUTPUT" and self.port.isdigit())
    
    def is_output_controller_action(self):
        return (self.type == "OUTPUT" and self.port=="CONTROLLER")
    
    
    def getInstruction(self, order):
        '''
        Gets the Instruction as an object (to be inserted in Flow actions list)
        Args:
            order:
                the order number of this instruction in the Flow list
        '''
        if self.json_instr is None:
            return None
        
        self.json_instr['order'] = order
        
        return self.json_instr
    
    
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
                output_to_port = a.port
            elif a.is_output_controller_action():
                output_to_controller = True
            elif a.is_drop_action():
                drop = True
            elif a.is_set_vlan_action():
                set_vlan_id = a.vlanId
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
    

 
    
class Selector(Match_Interface):
    def __init__(self, match = None):
        '''
        Represents any OpenFlow 1.0 possible matching rules for the incoming traffic
        '''
        self.type = None
        self.json_criteria = {} 
        
        self.port_in = None
        self.vlan_id = None
        self.eth_type = None        
        
        if match is not None:
            #TODO: add remaining match
            if match.vlan_id is not None:
                self.setVlanMatch(match.vlan_id)
            if match.ether_type is not None:
                self.setEtherTypeMatch(match.ether_type)
    
    
    def setInputMatch(self, in_port):
        self.type = 'IN_PORT'
        self.port_in = in_port
        
        self.json_criteria['PortIn'] = {}
        self.json_criteria['PortIn']['type'] = self.type
        self.json_criteria['PortIn']['port'] = self.port_in
        
    
    def setVlanMatch(self, vlan_id):
        self.type = 'VLAN_VID'
        self.vlan_id = vlan_id
        
        self.json_criteria['VlanID'] = {}
        self.json_criteria['VlanID']['type'] = self.type
        self.json_criteria['VlanID']['vlanId'] = self.vlan_id
        
        
    def setEtherTypeMatch(self, ethertype):
        self.type = 'ETH_TYPE'
        self.eth_type = ethertype
        
        self.json_criteria['EthType'] = {}
        self.json_criteria['EthType']['type'] = self.type
        self.json_criteria['EthType']['ethType'] = self.eth_type
        
    
    @property
    def InputPort(self):
        return self.port_in
    
    @property
    def VlanID(self):
        return self.vlan_id
    
    
    def getNffgMatch(self, nffg_flowrule):
        
        port_in = self.port_in
        ether_type = self.eth_type
        vlan_id = self.vlan_id
        
        # Not supported
        source_mac = None
        dest_mac = None
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
    

    def getCriteria(self):
        '''
        Gets the Criteria as an object (to be inserted in Flow actions list)
        Args:
            order:
                the order number of this action in the Flow list
        '''
        if len(self.json_criteria)==0:
            return None
        
        json_criteria = []
        for c in self.json_criteria.values():
            json_criteria.append(c)
        return json_criteria
