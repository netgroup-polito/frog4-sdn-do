"""
Created on 20/jun/2017

@author: gabrielecastellano
"""

import requests
import logging


class ConfigAgentRest:

    version = ""

    def __init__(self, version):
        self.version = version

    @staticmethod
    def __logging_debug(response, url, json_flow=None):
        log_string = "response: "+str(response.status_code)+", "+response.reason
        log_string = url+"\n"+log_string
        if json_flow is not None:
            log_string = log_string+"\n"+json_flow
        logging.debug(log_string)

    def push_configuration(self, config_agent_endpoint, user_id, graph_id, nf_id, json_config):
        headers = {'Accept': 'application/json', 'Content-type': 'application/json'}
        url = config_agent_endpoint+"/"+str(user_id)+"/"+str(graph_id)+"/"+str(nf_id)
        response = requests.put(url, json_config, headers=headers)

        self.__logging_debug(response, url, json_config)
        response.raise_for_status()
        return response.text
