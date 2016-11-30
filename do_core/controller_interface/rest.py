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
    def installApp(self, onos_endpoint, onos_user, onos_pass, app_filename):
        """
        Activate an application on top of the controller
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :param app_filename: the name of the file to install
        :return:
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

    @abstractmethod
    def check_ovsdbrest(self, onos_endpoint, onos_user, onos_pass):
        """
        Return OK if ovsdbrest API are at the moment available on the controller
        :param onos_endpoint: controller REST API address
        :param onos_user: controller user
        :param onos_pass: controller password for user
        :return:
        """
        pass

    @abstractmethod
    def add_port(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, bridge_name, port_name):
        """
        Add a physical port to an existing bridge through ovsdb
        :param onos_endpoint:
        :param onos_user:
        :param onos_pass:
        :param ovsdb_ip:
        :param bridge_name:
        :param port_name:
        :return:
        """
        pass

    @abstractmethod
    def add_gre_tunnel(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, bridge_name, port_name, local_ip, remote_ip,
                       key):
        """
        Add a port to an existing bridge through ovsdb and set up a gre tunnel on it
        :param onos_endpoint:
        :param onos_user:
        :param onos_pass:
        :param ovsdb_ip:
        :param bridge_name:
        :param port_name:
        :param local_ip:
        :param remote_ip:
        :param key:
        :return:
        """
        pass

    def delete_gre_tunnel(self, onos_endpoint, onos_user, onos_pass, ovsdb_ip, bridge_name, port_name):
        """
        Delete a gre port from a bridge through ovsdb
        :param onos_endpoint:
        :param onos_user:
        :param onos_pass:
        :param ovsdb_ip:
        :param bridge_name:
        :param port_name:
        :return:
        """
        pass
