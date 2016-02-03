'''
Created on 13/apr/2015

@author: vida
'''
import requests, logging

'''
######################################################################################################
###############################    OpenDaylight REST calls        ####################################
######################################################################################################
'''
class ODL_Rest(object):
    
    version=""
    
    def __init__(self, version):
        self.version=version
        if version == "Hydrogen":
            self.odl_nodes_path = "/controller/nb/v2/switchmanager/default/nodes"
            self.odl_controller_nodes_path = "/controller/nb/v2/connectionmanager/nodes"
            self.odl_topology_path = "/controller/nb/v2/topology/default"
            self.odl_flows_path = "/controller/nb/v2/flowprogrammer/default"
            self.odl_node="/node/OF"
            self.odl_flow="/staticFlow/"     
        else:
            self.odl_nodes_path = "/restconf/operational/opendaylight-inventory:nodes"
            #self.odl_controller_nodes_path = "???"
            self.odl_topology_path = "/restconf/operational/network-topology:network-topology/"
            self.odl_flows_path = "/restconf/config/opendaylight-inventory:nodes"
            self.odl_node="/node"
            self.odl_flow="/table/0/flow/"
    
    
    def __logging_debug(self, response, url, jsonFlow=None):
        log_string = "response: "+str(response.status_code)+", "+response.reason
        log_string = url+"\n"+log_string
        if jsonFlow is not None:
            log_string = log_string+"\n"+jsonFlow
        logging.debug(log_string)
            
            
    
    def getNodes(self, odl_endpoint, odl_user, odl_pass):
        '''
        Deprecated with Cisco switches because response is not a valid JSON
        '''
        headers = {'Accept': 'application/json'}
        url = odl_endpoint+self.odl_nodes_path
        response = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text
    
    
    
    def getControllerNodes(self, odl_endpoint, odl_user, odl_pass):
        '''
        Get the list of controlled nodes.
        '''
        if(self.version=="Hydrogen"):
            headers = {'Accept': 'application/json'}
            url = odl_endpoint+self.odl_controller_nodes_path
            response = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
            
            self.__logging_debug(response, url)
            response.raise_for_status()
            return response.text
        return None
    
    
    
    def getTopology(self, odl_endpoint, odl_user, odl_pass):
        '''
        Get the entire topology comprensive of hosts, switches and links (JSON)
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json'}
        url = odl_endpoint+self.odl_topology_path
        response = requests.get(url, headers=headers, auth=(odl_user, odl_pass))
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text
    
    
    
    def createFlow(self, odl_endpoint, odl_user, odl_pass, jsonFlow, switch_id, flow_id):
        '''
        Create a flow on the switch selected (Currently using OF1.0)
        Args:
            jsonFlow:
                JSON structure which describes the flow specifications
            switch_id:
                OpenDaylight id of the switch (example: openflow:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json', 'Content-type':'application/json'}
        url = odl_endpoint+self.odl_flows_path+self.odl_node+"/"+str(switch_id)+self.odl_flow+str(flow_id)
        response = requests.put(url,jsonFlow,headers=headers, auth=(odl_user, odl_pass))
        
        self.__logging_debug(response, url, jsonFlow)
        response.raise_for_status()
        return response.text
    
    
    
    def deleteFlow(self, odl_endpoint, odl_user, odl_pass, switch_id, flow_id):
        '''
        Delete a flow
        Args:
            switch_id:
                OpenDaylight id of the switch (example: openflow:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json', 'Content-type':'application/json'}
        url = odl_endpoint+self.odl_flows_path+self.odl_node+"/"+switch_id+self.odl_flow+str(flow_id)
        response = requests.delete(url,headers=headers, auth=(odl_user, odl_pass))
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text

