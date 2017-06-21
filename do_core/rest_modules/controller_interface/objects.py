'''
Created on 2/feb/2016

@author: giacomoratta
'''

from abc import ABCMeta, abstractmethod, abstractproperty

from nffg_library.nffg import Match as NffgMatch, Action as NffgAction

class Flow_Interface:
    
    '''
    Abstract class that defines the interface to be implemented on the controller flow object
    '''
    __metaclass__ = ABCMeta
    
    
    @abstractmethod
    def getJSON(self):
        '''
        Return a flow rule as json string ready to be installed in a switch.
        '''
        pass



class Action_Interface:
    
    '''
    Abstract class that defines the interface to be implemented on the controller action object
    '''
    __metaclass__ = ABCMeta
    
    
    @abstractproperty
    def OutputPort(self):
        pass
    
    @abstractproperty
    def VlanID(self):
        pass
    
    
    
    @abstractmethod
    def getNffgAction(self, actions, nffg_flowrule):
        '''
        Create a NFFG Action object 
        '''
        pass
    
    
    
    @abstractmethod
    def setDropAction(self):
        pass
    
    @abstractmethod
    def setControllerAction(self, max_length):
        pass
    
    @abstractmethod
    def setOutputAction(self, out_port, max_length):
        pass
    
    
        
    @abstractmethod
    def setPushVlanAction(self):
        pass
        
    @abstractmethod
    def setSwapVlanAction(self, vlan_id):
        pass
        
    @abstractmethod
    def setPopVlanAction(self):
        pass
    
    
    
    @abstractmethod
    def is_drop_action(self):
        pass
    
    @abstractmethod
    def is_output_port_action(self):
        pass
    
    @abstractmethod
    def is_output_controller_action(self):
        pass
    
    @abstractmethod
    def is_push_vlan_action(self):
        pass
    
    @abstractmethod
    def is_set_vlan_action(self):
        pass
    
    @abstractmethod
    def is_pop_vlan_action(self):
        pass




    
class Match_Interface:
    
    '''
    Abstract class that defines the interface to be implemented on the controller match object
    '''
    __metaclass__ = ABCMeta
    
    
    @abstractproperty
    def InputPort(self):
        return self.port_in
    
    @abstractproperty
    def VlanID(self):
        return self.vlan_id
    
    
    
    @abstractmethod
    def getNffgMatch(self, nffg_flowrule):
        '''
        Create a NFFG Match object 
        '''
        pass
    
    
    
    @abstractmethod
    def setInputMatch(self, in_port):
        pass
    
    @abstractmethod
    def setVlanMatch(self, vlan_id):
        pass
    
    @abstractmethod
    def setEtherTypeMatch(self, ethertype):
        pass

