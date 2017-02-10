"""
Created on 02 sep 2016
@author: gabrielecastellano
"""
import json


class DomainInfo(object):
    def __init__(self, domain_id=None, name=None, _type=None, domain_ip=None, domain_port=None,
                 hardware_info=None, capabilities=None, interfaces=None):
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
        self.interfaces = interfaces or []

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

    def get_dict(self):
        domain_info_dict = {}
        domain_info_dict['netgroup-domain:informations'] = {}
        domain_info_dict['netgroup-domain:informations']['id'] = self.domain_id
        domain_info_dict['netgroup-domain:informations']['name'] = self.name
        domain_info_dict['netgroup-domain:informations']['type'] = self.type
        domain_info_dict['netgroup-domain:informations']['management-address'] = self.domain_ip + ':' + self.domain_port

        if self.hardware_info is not None:
            domain_info_dict['netgroup-domain:informations']['hardware-informations'] = self.hardware_info.get_dict()
        if self.capabilities is not None:
            domain_info_dict['netgroup-domain:informations']['capabilities'] = self.capabilities.get_dict()

        return domain_info_dict

    @staticmethod
    def get_from_file(file_name):
        """
        :param file_name: name of json file in the /config folder
        :type file_name: str
        :return: DomainInfo object
        :rtype: DomainInfo
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

    def get_dict(self):
        hardware_info_dict = {}
        if self.resources is not None:
            hardware_info_dict['resources'] = self.resources.get_dict()
        interfaces = []
        for interface in self.interfaces:
            interfaces.append(interface.get_dict())
        if len(interfaces) > 0:
            hardware_info_dict['interfaces'] = {}
            hardware_info_dict['interfaces']['interface'] = interfaces

        return hardware_info_dict

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

    def get_dict(self):
        resources_dict = {}
        if self.cpu is not None:
            resources_dict['cpu'] = self.cpu.get_dict()
        if self.memory is not None:
            resources_dict['memory'] = self.memory.get_dict()
        if self.storage is not None:
            resources_dict['storage'] = self.storage.get_dict()

        return resources_dict


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

    def get_dict(self):
        cpu_dict = {}
        cpu_dict['number'] = self.number
        cpu_dict['frequency'] = self.frequency
        cpu_dict['free'] = self.free

        return cpu_dict


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

    def get_dict(self):
        memory_dict = {}
        memory_dict['size'] = self.size
        memory_dict['frequency'] = self.frequency
        memory_dict['latency'] = self.latency
        memory_dict['free'] = self.free

        return memory_dict


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

    def get_dict(self):
        storage_dict = {}
        storage_dict['size'] = self.size
        storage_dict['latency'] = self.latency
        storage_dict['free'] = self.free

        return storage_dict


class Interface(object):
    # Subinterfaces are ignored
    def __init__(self, index=None, node=None, name=None, side=None, enabled=None, neighbors=None, gre=False, gre_tunnels=None,
                 vlan=False, vlan_mode=None, vlans_free=None):
        """
        :param index: subinterface index
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
        :type index: int
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
        self.index = index
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
        self.index = interface_dict['index']
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
                    self.gre = subinterface_dict['netgroup-if-capabilities:capabilities']['netgroup-if-capabilities:gre']
                    if self.gre:
                        if 'netgroup-if-gre:gre' in subinterface_dict:
                            for gre_dict in subinterface_dict['netgroup-if-gre:gre']:
                                gre_tunnel = GreTunnel()
                                gre_tunnel.parse_dict(gre_dict)
                                self.gre_tunnels.append(gre_tunnel)
        if 'netgroup-neighbor:neighbors' in interface_dict:
            for neighbor_dict in interface_dict['netgroup-neighbor:neighbors']['netgroup-neighbor:neighbor']:
                neighbor = Neighbor()
                neighbor.parse_dict(neighbor_dict)
                self.neighbors.append(neighbor)

        if 'netgroup-if-ethernet:ethernet' in interface_dict:
            if 'netgroup-vlan:vlans' in interface_dict['netgroup-if-ethernet:ethernet']:
                self.vlan = True
                for vlan_dict in interface_dict['netgroup-if-ethernet:ethernet']['netgroup-vlan:vlans'][
                        'netgroup-vlan:vlan']:
                    self.vlans_free.append(vlan_dict['netgroup-vlan:vlan-id'])
                ''' - old way, does not follow openconfig model
                if 'netgroup-vlan:config' in interface_dict['openconfig-if-ethernet:ethernet'][
                        'openconfig-vlan:vlan']:
                    vlan_config = interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan'][
                            'openconfig-vlan:config']
                    self.vlan_mode = vlan_config['interface-mode']
                    if vlan_config['interface-mode'] == 'TRUNK':
                        for vlan in vlan_config['trunk-vlans']:
                            self.vlans_free.append(vlan)
                '''

    def get_dict(self):
        interface_dict = {}
        interface_dict['index'] = self.index
        if self.node is not None:
            interface_dict['name'] = self.node + '/' + self.name
        else:
            interface_dict['name'] = self.name
        if self.side is not None:
            interface_dict['side'] = self.side
        interface_dict['config'] = {}
        interface_dict['config']['enabled'] = self.enabled

        interface_dict['subinterfaces'] = {}
        interface_dict['subinterfaces']['subinterface'] = []
        subinterface_dict = {}
        subinterface_dict['config'] = {}
        subinterface_dict['config']['name'] = self.name
        subinterface_dict['netgroup-if-capabilities:capabilities'] = {}
        subinterface_dict['netgroup-if-capabilities:capabilities']['netgroup-if-capabilities:gre'] = self.gre
        gre_tunnels = []
        for gre_tunnel in self.gre_tunnels:
            gre_tunnels.append(gre_tunnel.get_dict())
        subinterface_dict['netgroup-if-gre:gre'] = gre_tunnels
        interface_dict['subinterfaces']['subinterface'].append(subinterface_dict)

        neighbors = []
        for neighbor in self.neighbors:
            neighbors.append(neighbor.get_dict())
        if len(neighbors) > 0:
            interface_dict['netgroup-neighbor:neighbors'] = {}
            interface_dict['netgroup-neighbor:neighbors']['netgroup-neighbor:neighbor'] = neighbors

        if self.vlan:
            ''' - old way, does not follow openconfig model
            if self.vlan_mode:
                config_dict = {}
                config_dict['interface-mode'] = self.vlan_mode
                if self.vlan_mode == 'TRUNK':
                    trunk_vlans = []
                    for vlan in self.vlans_free:
                        trunk_vlans.append(vlan)
                    config_dict['trunk-vlans'] = trunk_vlans
                interface_dict['openconfig-if-ethernet:ethernet'] = {}
                interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan'] = {}
                interface_dict['openconfig-if-ethernet:ethernet']['openconfig-vlan:vlan'][
                    'openconfig-vlan:config'] = config_dict
            '''
            interface_dict['netgroup-if-ethernet:ethernet'] = {}
            vlans = []
            for vlan_id in self.vlans_free:
                vlan_dict = {'netgroup-vlan:vlan-id': vlan_id}
                config_dict = {'netgroup-vlan:vlan-id': vlan_id}
                vlan_dict['netgroup-vlan:config'] = config_dict
                vlans.append(vlan_dict)
            interface_dict['netgroup-if-ethernet:ethernet']['netgroup-vlan:vlans'] = {}
            interface_dict['netgroup-if-ethernet:ethernet']['netgroup-vlan:vlans']['netgroup-vlan:vlan'] = vlans

        return interface_dict

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

    def get_dict(self):
        neighbor_dict = {}
        neighbor_dict['domain-name'] = self.domain_name
        if self.remote_interface is not None:
            if self.node is not None:
                neighbor_dict['remote-interface'] = self.node + '/' + self.remote_interface
            else:
                neighbor_dict['remote-interface'] = self.remote_interface
        if self.neighbor_type is not None:
            neighbor_dict['neighbor-type'] = self.neighbor_type

        return neighbor_dict


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

    def get_dict(self):
        gre_dict = {}
        gre_dict['name'] = self.name

        if self.local_ip is not None:
            gre_dict['local_ip'] = self.local_ip
        if self.remote_ip is not None:
            gre_dict['remote_ip'] = self.remote_ip
        if self.gre_key is not None:
            gre_dict['key'] = self.gre_key

        return gre_dict


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

    def get_dict(self):
        capabilities_dict = {}
        infrastructural_capabilities = []
        for ic in self.infrastructural_capabilities:
            infrastructural_capabilities.append(ic.get_dict())
        capabilities_dict['infrastructural-capabilities'] = {}
        capabilities_dict['infrastructural-capabilities']['infrastructural-capability'] = infrastructural_capabilities
        functional_capabilities = []
        for fc in self.functional_capabilities:
            functional_capabilities.append(fc.get_dict())
        capabilities_dict['functional-capabilities'] = {}
        capabilities_dict['functional-capabilities']['functional-capability'] = functional_capabilities
        return capabilities_dict


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

    def get_dict(self):
        ic_dict = {}
        ic_dict['type'] = self.type
        ic_dict['name'] = self.name

        return ic_dict


class FunctionalCapability(object):
    def __init__(self, _type=None, name=None, ready=False, family=None, template=None, resources=None, function_specifications=None):
        """
        :param _type:
        :param name:
        :param ready:
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
        self.ready = ready
        self.family = family
        self.template = template
        self.resources = resources
        self.function_specifications = function_specifications or []

    def parse_dict(self, functional_capability_dict):
        self.type = functional_capability_dict['type']
        self.name = functional_capability_dict['name']
        self.ready = functional_capability_dict['ready']
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

    def get_dict(self):
        fc_dict = {}
        fc_dict['type'] = self.type
        fc_dict['name'] = self.name
        fc_dict['ready'] = self.ready
        if self.family is not None:
            fc_dict['family'] = self.family
        if self.template is not None:
            fc_dict['template'] = self.template
        if self.resources is not None:
            fc_dict['resources'] = self.resources.get_dict()
        function_specifications = []
        for fs in self.function_specifications:
            function_specifications.append(fs.get_dict())
        fc_dict['function-specifications'] = {}
        fc_dict['function-specifications']['function-specification'] = function_specifications
        return fc_dict


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

    def get_dict(self):
        fc_dict = {}
        fc_dict['name'] = self.name
        fc_dict['value'] = self.value
        fc_dict['unit'] = self.unit
        fc_dict['mean'] = self.mean

        return fc_dict
