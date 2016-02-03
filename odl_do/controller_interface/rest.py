'''
Created on 3/feb/2016

@author: giacomoratta
'''

from abc import ABCMeta, abstractmethod, abstractproperty


class Rest_Interface:  
    
    '''
    Abstract class that defines the interface to be implemented on the controller rest calls
    '''
    __metaclass__ = ABCMeta
    
    
    @abstractmethod
    def createFlow(self, onos_endpoint, onos_user, onos_pass, jsonFlow, switch_id, flow_id):
        '''
        Create a flow on the switch selected (Currently using OF1.0)
        Args:
            jsonFlow:
                JSON structure which describes the flow specifications
            switch_id:
                ID of the switch (example: of:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        pass
    
    
    @abstractmethod
    def deleteFlow(self, onos_endpoint, onos_user, onos_pass, switch_id, flow_id):
        '''
        Delete a flow
        Args:
            switch_id:
                ID of the switch (example: of:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        pass

