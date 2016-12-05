"""
Created on 28/nov/2016

@author: paolomagliona
"""


import requests
import logging
import json
from do_core.controller_interface.rest import RestInterface
import os


class VNF_Repository_Rest(RestInterface):
    version = ""

    def __init__(self):
        self.vnf_get_capability_url = '/v2/nf_capability'
        pass

    def __logging_debug(self, response, url, jsonFlow=None):
        log_string = "response: " + str(response.status_code) + ", " + response.reason
        log_string = url + "\n" + log_string
        if jsonFlow is not None:
            log_string = log_string + "\n" + jsonFlow
        logging.debug(log_string)

    def get_vnf_template(self, template_uri):
        """
        Return the template from the specified uri
        :param template_uri: the uri of the template
        :return:
        """
        headers = {'Accept': 'application/json'}
        url = template_uri

        response = requests.get(url, headers=headers)
        # response = True

        self.__logging_debug(response, url)
        response.raise_for_status()
        return response

    def get_vnfs_list(self, vnf_repository_endpoint, vnf_name):
        """
        Return the list of templates for the specified vnf
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_name: the application name
        :return:
        """
        headers = {'Accept': 'application/json'}
        url = vnf_repository_endpoint + self.vnf_get_capability_url + "/" + str(vnf_name.lower()) + "/"

        response = requests.get(url, headers=headers)
        #response = True

        self.__logging_debug(response, url)
        response.raise_for_status()
        return response


    def get_vnf_image_from_uri(self, vnf_image_uri):
        """
        Return the name of the vnf image downloaded from the specified uri
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_name: the application name
        :return:
        """

        vnf_image_filename = os.path.basename(vnf_image_uri)
        logging.debug("File name from uri: %s", vnf_image_filename)
        cur_path = os.getcwd()
        #logging.debug("Current path vnf get: %s", cur_path)

        url = vnf_image_uri + "/"  # the last / is added for the get request

        response = requests.get(url, stream=True)
        response.raise_for_status()

        bundledir = os.path.join(cur_path, 'bundles')
        filename = os.path.join(cur_path, 'bundles', vnf_image_filename)
        logging.debug("Path for downloading file: %s", filename)

        if not os.path.exists(bundledir): #if the folder bundles doesn't exists, create it
            os.makedirs(bundledir)

        with open(filename, 'wb') as fd:
            for chunk in response.iter_content(chunk_size=1024):
                fd.write(chunk)
        self.__logging_debug(response, url)
        # return response.text
        return vnf_image_filename #return the name of the file downloaded

