"""
Created on 02 sep 2016
@author: gabrielecastellano
"""
import json


class DomainInfo(object):
    def __init__(self, domain_id=None, name=None, _type=None, domain_ip=None, domain_port=None,
                 hardware_info=None, capabilities=None):
        """

        :param domain_id:
        :param name:
        :param _type:
        :param domain_ip:
        :param domain_port:
        :param hardware_info:
        :param capabilities:
        :type domain_id: str
        :type name: str
        :type _type: str
        :type domain_ip: str
        :type domain_port: str
        :type hardware_info: HardwareInfo
        :type capabilities: Capabilities
        """
        self.domain_id = domain_id
        self.name = name
        self.type = _type
        self.domain_ip = domain_ip
        self.domain_port = domain_port
        self.hardware_info = hardware_info
        self.capabilities = capabilities
        # self.interfaces = interfaces or []

    def parse_dict(self, domain_info_dict):
        self.domain_id = domain_info_dict['netgroup-domain:informations']['id']
        self.name = domain_info_dict['netgroup-domain:informations']['name']
        self.type = domain_info_dict['netgroup-domain:informations']['type']
        management_address = domain_info_dict['netgroup-domain:informations']['management-address']
        tmp = management_address.split(':')
        self.domain_ip = tmp[0]
        self.domain_port = tmp[1]

        if 'hardware-informations' in domain_info_dict['netgroup-domain:informations']:
            self.hardware_info = HardwareInfo()
            self.hardware_info.parse_dict(domain_info_dict['netgroup-domain:informations']['hardware-informations'])
        if 'capabilities' in domain_info_dict['netgroup-domain:informations']:
            self.capabilities = Capabilities()
            self.capabilities.parse_dict(domain_info_dict['netgroup-domain:informations']['capabilities'])

    @staticmethod
    def get_from_file(file_name):
        """

        :param file_name: name of json file in the /config folder
        :type file_name: str
        :return: DomainInfo
        """

        json_data = open(file_name).read()
        domain_info_dict = json.loads(json_data)
        # TODO validation
        domain_info = DomainInfo()
        domain_info.parse_dict(domain_info_dict)
        return domain_info


class HardwareInfo(object):
    def __init__(self, resources=None, interfaces=None):
        """

        :param resources:
        :param interfaces:
        :type resources: Resources
        :type interfaces: list of Interface
        """
        self.resources = resources
        self.interfaces = interfaces or []

    def parse_dict(self, hardware_info_dict):
        if 'resources' in hardware_info_dict:
            self.resources = Resources()
            self.resources.parse_dict(hardware_info_dict['resources'])
        if 'interfaces' in hardware_info_dict:
            for interface_dict in hardware_info_dict['interfaces']['interface']:
                interface = Interface()
                interface.parse_dict(interface_dict)
                if interface.enabled is True:
                    self.interfaces.append(interface)

    def add_interface(self, interface):
        if type(interface) is Interface:
            self.interfaces.append(interface)
        else:
            raise TypeError("Tried to add an interface with a wrong type. Expected Interface, found " + type(interface))

    def get_interface(self, node, name):
        for interface in self.interfaces:
            if interface.node == node and interface.name == name:
                return interface


class Resources(object):
    def __init__(self, cpu=None, memory=None, storage=None):
        """

        :param cpu:
        :param memory:
        :param storage:
        :type cpu: Cpu
        :type memory: Memory
        :type storage: Storage
        """
        self.cpu = cpu
        self.memory = memory
        self.storage = storage

    def parse_dict(self, resources_dict):
        if 'cpu' in resources_dict:
            self.cpu = Cpu()
            self.cpu.parse_dict(resources_dict['cpu'])
        if 'memory' in resources_dict:
            self.memory = Memory()
            self.memory.parse_dict(resources_dict['memory'])
        if 'storage' in resources_dict:
            self.storage = Storage()
            self.storage.parse_dict(resources_dict['storage'])


class Cpu(object):
    def __init__(self, number=None, frequency=None, free=None):
        """

        :param number:
        :param frequency:
        :param free:
        :type number: int
        :type frequency: int
        :type free: int
        """
        self.number = number
        self.frequency = frequency
        self.free = free

    def parse_dict(self, cpu_dict):
        self.number = cpu_dict['number']
        self.frequency = cpu_dict['frequency']
        self.free = cpu_dict['free']


class Memory(object):
    def __init__(self, size=None, frequency=None, latency=None, free=None):
        """

        :param size:
        :param frequency:
        :param latency:
        :param free:
        :type size: int
        :type frequency: int
        :type latency: int
        :type free: int
        """
        self.size = size
        self.frequency = frequency
        self.latency = latency
        self.free = free

    def parse_dict(self, memory_dict):
        self.size = memory_dict['size']
        self.frequency = memory_dict['frequency']
        self.latency = memory_dict['latency']
        self.free = memory_dict['free']


class Storage(object):
    def __init__(self, size=None, latency=None, free=None):
        """

        :param size:
        :param latency:
        :param free:
        :type size: int
        :type latency: int
        :type free: int
        """
        self.size = size
        self.latency = latency
        self.free = free

    def parse_dict(self, storage_dict):
        self.size = storage_dict['size']
        self.latency = storage_dict['latency']
        self.free = storage_dict['free']


class Interface(object):
    # Subinterfaces are ignored
    def __init__(self, node=None, name=None, side=None, enabled=None, neighbors=None, gre=False, gre_tunnels=None,
                 vlan=False, vlan_mode=None, vlans_free=None):
        """

        :param node: ip address
        :param name: interface name
        :param side:
        :param enabled:
        :param neighbors:
        :param gre:
        :param gre_tunnels:
        :param vlan:
        :param vlan_mode:
        :param vlans_free:
        :type node: str
        :type name: str
        :type side: str
        :type enabled: bool
        :type neighbors: list of Neighbor
        :type gre: bool
        :type gre_tunnels: list of GreTunnel
        :type vlan: bool
        :type vlan_mode: str
        :type vlans_free: list of int
        """
        self.node = node
        self.name = name
        self.side = side
        self.enabled = enabled
        self.gre = gre
        self.gre_tunnels = gre_tunnels or []
        self.vlan = vlan
        self.vlan_mode = vlan_mode
        self.vlans_free = vlans_free or []
        self.neighbors = neighbors or []

    def parse_dict(self, interface_dict):
        if '/' in interface_dict['name']:
            tmp = interface_dict['name']
            self.node = tmp.split('/')[0]
            self.name = tmp.split('/')[1]
        else:
            self.name = interface_dict['name']
        if 'netgroup-if-side:side' in interface_dict:
            self.side = interface_dict['netgroup-if-side:side']
        self.enabled = interface_dict['config']['enabled']

        if 'subinterfaces' in interface_dict:
            for subinterface_dict in interface_dict['subinterfaces']['subinterface']:
                if subinterface_dict['config']['name'] == self.name:
                    if subinterface_dict['netgroup-if-capabilities:capabilities']['gre']:
                        self.gre = True
                        if 'frog-if-gre:gre' in subinterface_dict:
                            for gre_dict in subinterface_dict['netgroup-if-gre:gre']:
                                gre_tunnel = GreTunnel()
                                gre_tunnel.parse_dict(gre_dict)
                                self.gre_tunnels.append(gre_tunnel)
        if 'netgroup-neighbor:neighbors' in interface_dict:
            for neighbor_dict in interface_dict['netgroup-neighbor:neighbors']['netgroup-neighbor:neighbor']:
                neighbor = Neighbor()
                neighbor.parse_dict(neighbor_dict)
                self.neighbors.append(neighbor)

        if 'openconfig-if-ethernet:ethernet' in interface_dict:
            if 'openconfig-vlan:vlan' in interface_dict['openconfig-if-ethernet:ethernet']:
                self.vlan = True
                if 'openconfig-vlan:config' in interface_dict['openconfig-if-ethernet:ethernet'][
                        'openconfig-vlan:vlan']:
                    vlan_config = interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan'][
                            'openconfig-vlan:config']
                    self.vlan_mode = vlan_config['interface-mode']
                    if vlan_config['interface-mode'] == 'TRUNK':
                        for vlan in vlan_config['trunk-vlans']:
                            self.vlans_free.append(vlan)

    def add_neighbor(self, neighbor):
        if type(neighbor) is Neighbor:
            self.neighbors.append(neighbor)
        else:
            raise TypeError("Tried to add a neighbor with a wrong type. Expected Neighbor, found " + type(neighbor))

    def add_gre_tunnel(self, gre_tunnel):
        if type(gre_tunnel) is GreTunnel:
            self.gre_tunnels.append(gre_tunnel)
        else:
            raise TypeError(
                "Tried to add a gre tunnel with a wrong type. Expected GreTunnel, found " + type(gre_tunnel))

    def add_vlan(self, vlan):
        self.vlans_free.append(vlan)


class Neighbor(object):
    def __init__(self, domain_name=None, remote_interface=None, neighbor_type=None, node=None):
        """

        :param domain_name:
        :param remote_interface:
        :param neighbor_type:
        :param node:
        :type domain_name: str
        :type remote_interface: str
        :type neighbor_type: str
        :type node: str
        """
        self.domain_name = domain_name
        self.remote_interface = remote_interface
        self.neighbor_type = neighbor_type
        self.node = node

    def parse_dict(self, neighbor_dict):
        self.domain_name = neighbor_dict['domain-name']
        if 'remote-interface' in neighbor_dict:
            if '/' in neighbor_dict['remote-interface']:
                tmp = neighbor_dict['remote-interface']
                self.node = tmp.split('/')[0]
                self.remote_interface = tmp.split('/')[1]
            else:
                self.remote_interface = neighbor_dict['remote-interface']
        if 'neighbor-type' in neighbor_dict:
            self.neighbor_type = neighbor_dict['neighbor-type']


class GreTunnel(object):
    def __init__(self, name=None, local_ip=None, remote_ip=None, gre_key=None):
        """

        :param name:
        :param local_ip:
        :param remote_ip:
        :param gre_key:
        :type name: str
        :type local_ip: str
        :type remote_ip: str
        :type gre_key: str
        """
        self.name = name
        self.local_ip = local_ip
        self.remote_ip = remote_ip
        self.gre_key = gre_key

    def parse_dict(self, gre_dict):
        self.name = gre_dict['name']
        if 'local_ip' in gre_dict['options']:
            self.local_ip = gre_dict['options']['local_ip']
        if 'remote_ip' in gre_dict['options']:
            self.remote_ip = gre_dict['options']['remote_ip']
        if 'key' in gre_dict['options']:
            self.gre_key = gre_dict['options']['key']


class Capabilities(object):
    def __init__(self, infrastructural_capabilities=None, functional_capabilities=None):
        """

        :param infrastructural_capabilities:
        :param functional_capabilities:
        :type infrastructural_capabilities: list of InfrastructuralCapability
        :type functional_capabilities: list of FunctionalCapability
        """
        self.infrastructural_capabilities = infrastructural_capabilities or []
        self.functional_capabilities = functional_capabilities or []

    def parse_dict(self, capabilities_dict):
        if 'infrastructural-capabilities' in capabilities_dict:
            for infr_capability_dict in capabilities_dict['infrastructural-capabilities']['infrastructural-capability']:
                infrastructural_capability = InfrastructuralCapability()
                infrastructural_capability.parse_dict(infr_capability_dict)
                self.infrastructural_capabilities.append(infrastructural_capability)
        if 'functional-capabilities' in capabilities_dict:
            for func_capability_dict in capabilities_dict['functional-capabilities']['functional-capability']:
                functional_capability = FunctionalCapability()
                functional_capability.parse_dict(func_capability_dict)
                self.functional_capabilities.append(functional_capability)


class InfrastructuralCapability(object):
    def __init__(self, _type=None, name=None):
        """

        :param _type:
        :param name:
        :type _type: str
        :type name: str
        """
        self.type = _type
        self.name = name

    def parse_dict(self, infrastructural_capability_dict):
        self.type = infrastructural_capability_dict['type']
        self.name = infrastructural_capability_dict['name']


class FunctionalCapability(object):
    def __init__(self, _type=None, name=None, family=None, template=None, resources=None, function_specifications=None):
        """

        :param _type:
        :param name:
        :param family:
        :param template:
        :param resources:
        :param function_specifications:
        :type _type: str
        :type name: str
        :type family: str
        :type template: str
        :type resources: Resources
        :type function_specifications: list of FunctionSpecification
        """
        self.type = _type
        self.name = name
        self.family = family
        self.template = template
        self.resources = resources
        self.function_specifications = function_specifications or []

    def parse_dict(self, functional_capability_dict):
        self.type = functional_capability_dict['type']
        self.name = functional_capability_dict['name']
        if 'family' in functional_capability_dict:
            self.family = functional_capability_dict['family']
        if 'template' in functional_capability_dict:
            self.template = functional_capability_dict['template']
        if 'resources' in functional_capability_dict:
            self.resources = Resources()
            self.resources.parse_dict(functional_capability_dict['resources'])
        if 'function-specifications' in functional_capability_dict:
            for function_spec_dict in functional_capability_dict['function-specifications']['function-specification']:
                function_specification = FunctionSpecification()
                function_specification.parse_dict(function_spec_dict)
                self.function_specifications.append(function_specification)


class FunctionSpecification(object):
    def __init__(self, name=None, value=None, unit=None, mean=None):
        """

        :param name:
        :param value:
        :param unit:
        :param mean:
        :type name: str
        :type value: str
        :type unit: str
        :type mean: str
        """
        self.name = name
        self.value = value
        self.unit = unit
        self.mean = mean

    def parse_dict(self, function_specification_dict):
        self.name = function_specification_dict['name']
        self.value = function_specification_dict['value']
        self.unit = function_specification_dict['unit']
        self.mean = function_specification_dict['mean']
