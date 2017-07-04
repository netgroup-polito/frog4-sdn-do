"""
Created on 20/jun/2017

@author: gabrielecastellano
"""

import requests
import logging


class ConfigServiceRest:

    def __init__(self):

        self.config = '/config'
        self.config_files = '/config/files'
        self.config_default = '/config/files'

    @staticmethod
    def __logging_debug(response, url, json_flow=None):
        log_string = "response: "+str(response.status_code)+", "+response.reason
        log_string = url+"\n"+log_string
        if json_flow is not None:
            log_string = log_string+"\n"+json_flow
        logging.debug(log_string)

    # not used
    def get_file_list(self, config_service_endpoint, user_id, graph_id, nf_id):
        headers = {'Accept': 'application/json'}
        url = config_service_endpoint+self.config_files+"/"+str(user_id)+"/"+str(graph_id)+"/"+str(nf_id)
    
        response = requests.get(url, headers=headers)
        
        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text

    def get_file(self, config_service_endpoint, user_id, graph_id, nf_id, file):
        headers = {'Accept': 'application/json'}
        url = config_service_endpoint+self.config_files+"/"+str(user_id)+"/"+str(graph_id)+"/"+str(nf_id)+"/"+str(file)

        response = requests.get(url, headers=headers)

        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text

    def get_default_file(self, config_service_endpoint, functional_capability, file):
        headers = {'Accept': 'application/json'}
        url = config_service_endpoint+self.config_files+"/"+str(functional_capability)+"/"+str(file)

        response = requests.get(url, headers=headers)

        self.__logging_debug(response, url)
        response.raise_for_status()
        return response.text

    def push_config(self, config_service_endpoint, user_id, graph_id, nf_id, json_config):

        headers = {'Accept': 'application/json', 'Content-type': 'application/json'}
        url = config_service_endpoint+self.config+"/"+str(user_id)+"/"+str(graph_id)+"/"+str(nf_id)
        response = requests.put(url, json_config, headers=headers)

        self.__logging_debug(response, url, json_config)
        response.raise_for_status()
        return response.text
