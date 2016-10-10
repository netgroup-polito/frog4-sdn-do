'''
Created on 3/feb/2016

@author: giacomoratta
'''

from abc import ABCMeta, abstractmethod, abstractproperty

class RestInterface:

    """
    Abstract class that defines the interface to be implemented on the controller rest calls
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def createFlow(self, onos_endpoint, onos_user, onos_pass, jsonFlow, switch_id, flow_id):
        """
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
        """
        pass

    @abstractmethod
    def deleteFlow(self, onos_endpoint, onos_user, onos_pass, switch_id, flow_id):
        """
        Delete a flow
        Args:
            switch_id:
                ID of the switch (example: of:1234567890)
            flow_id:
                OpenFlow id of the flow
        Exceptions:
            raise the requests.HTTPError exception connected to the REST call in case of HTTP error
        """
        pass

    @abstractmethod
    def activateApp(self, onos_endpoint, onos_user, onos_pass, app_name):
        """
        Activate an application on top of the controller
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_name: the application to activate
        :return:
        """
        pass

    @abstractmethod
    def deactivateApp(self, onos_endpoint, onos_user, onos_pass, app_name):
        """
        Deactivate an application running on top of the controller
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_name: the application to activate
        :return:
        """
        pass

    @abstractmethod
    def push_config(self, onos_endpoint, onos_user, onos_pass, json_config):
        """
        Push a configuration to onos through network config API
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param json_config: the configuration to push
        :return:
        """
        pass

    @abstractmethod
    def get_applications_capabilities(self, onos_endpoint, onos_user, onos_pass):
        """
        Return the whole set of applications capabilities
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :return:
        """
        pass

    @abstractmethod
    def get_application_capability(self, onos_endpoint, onos_user, onos_pass, app_name):
        """
        Return the capability of a specific application if any
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_name: the application name
        :return:
        """
        pass
