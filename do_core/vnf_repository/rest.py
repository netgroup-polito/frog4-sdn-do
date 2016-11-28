"""
Created on 28/nov/2016

@author: paolomagliona
"""


import requests
import logging
import json
from do_core.controller_interface.rest import RestInterface


class VNF_Repository_Rest(RestInterface):
    version = ""

    def __init__(self):
        self.vnf_repository_url = '/vnf'
        pass

    def __logging_debug(self, response, url, jsonFlow=None):
        log_string = "response: " + str(response.status_code) + ", " + response.reason
        log_string = url + "\n" + log_string
        if jsonFlow is not None:
            log_string = log_string + "\n" + jsonFlow
        logging.debug(log_string)

    def get_vnf(self, vnf_repository_endpoint, vnf_name):
        """
        Return the information of a specific vnf if any
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_name: the application name
        :return:
        """
        headers = {'Accept': 'application/json'}
        url = vnf_repository_endpoint + self.vnf_repository_url + "/" + str(vnf_name)

        #response = requests.get(url, headers=headers, auth=(vnf_repository_user, vnf_repository_pass))
        response = True

        #self.__logging_debug(response, url)
        #response.raise_for_status()
        #return response.text
        return response


