'''
Created on 2/feb/2016

@author: giacomoratta
'''
import requests, logging

'''
######################################################################################################
###################################      ONOS REST calls      ########################################
######################################################################################################
'''
class ONOS_Rest(object):
    
    version=""
    
    def __init__(self, version):
        self.version=version
        
        self.rest_devices_url = '/onos/v1/devices'
        self.rest_links_url = '/onos/v1/links'
        self.rest_flows_url = '/onos/v1/flows' #/onos/v1/flows/{DeviceId}
    
    
    def __logging_debug(self, response, url, jsonFlow=None):
        log_string = "response: "+str(response.status_code)+", "+response.reason
        log_string = url+"\n"+log_string
        if jsonFlow is not None:
            log_string = log_string+"\n"+jsonFlow
        logging.debug(log_string)
    
    
    def getDevices(self, onos_endpoint, onos_user, onos_pass):
        headers = {'Accept': 'application/json'}
        url = onos_endpoint+self.rest_devices_url
    
        response = requests.get(url, headers=headers, auth=(onos_user, onos_pass))
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text
    
    
    def getLinks(self, onos_endpoint, onos_user, onos_pass):
        headers = {'Accept': 'application/json'}
        url = onos_endpoint+self.rest_links_url
    
        response = requests.get(url, headers=headers, auth=(onos_user, onos_pass))
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text
    
    
    
    def createFlow(self, onos_endpoint, onos_user, onos_pass, jsonFlow, switch_id):
        '''
        Create a flow on the switch selected (Currently using OF1.0)
        Args:
            jsonFlow:
                JSON structure which describes the flow specifications
            switch_id:
                ONOS id of the switch (example: of:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json', 'Content-type':'application/json'}
        url = onos_endpoint+self.rest_flows_url+"/"+str(switch_id)
        response = requests.post(url,jsonFlow,headers=headers, auth=(onos_user, onos_pass))
        
        self.__logging_debug(response, url, jsonFlow)
        response.raise_for_status()
        
        location = str(response.headers['location']).split("/")
        flow_id = location[len(location)-1] 
        
        return flow_id, response.text
    
    
    
    def deleteFlow(self, onos_endpoint, onos_user, onos_pass, switch_id, flow_id):
        '''
        Delete a flow
        Args:
            switch_id:
                ONOS id of the switch (example: of:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        '''
        headers = {'Accept': 'application/json', 'Content-type':'application/json'}
        url = onos_endpoint+self.rest_flows_url+"/"+str(switch_id)+"/"+str(flow_id)
        response = requests.delete(url,headers=headers, auth=(onos_user, onos_pass))
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text

