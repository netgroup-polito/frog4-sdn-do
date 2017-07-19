'''
Created on Nov 10, 2015

@author: giacomo
'''

import json

import networkx as nx

from do_core.config import Configuration
from domain_information_library.domain_info import FunctionalCapability
from nffg_library.nffg import NF_FG, EndPoint

if Configuration().CONTROLLER_NAME == "OpenDayLight":
    from do_core.rest_modules.odl import Flow, Match, Action
    from do_core.rest_modules.odl import ODL_Rest
    
elif Configuration().CONTROLLER_NAME == "ONOS":
    from do_core.rest_modules.onos.objects import Flow, Selector as Match, Treatment as Action
    from do_core.rest_modules.onos.rest import ONOS_Rest
        

class NetManager:

    def __init__(self):

        self.nffg_id = None
        self.user = None
        
        # Controller (ODL, ONOS, etc.)
        self.ct_name = Configuration().CONTROLLER_NAME
        
        if self.ct_name == 'OpenDayLight':
            self.ct_endpoint = Configuration().ODL_ENDPOINT
            self.ct_version = Configuration().ODL_VERSION
            self.ct_username = Configuration().ODL_USERNAME
            self.ct_password = Configuration().ODL_PASSWORD
            
        elif self.ct_name == 'ONOS':
            self.ct_endpoint = Configuration().ONOS_ENDPOINT
            self.ct_version = Configuration().ONOS_VERSION
            self.ct_username = Configuration().ONOS_USERNAME
            self.ct_password = Configuration().ONOS_PASSWORD
        
        # Topology
        self.topology = None  # nx.Graph()
        self.WEIGHT_PROPERTY_NAME = 'weight'
        self.ACTIONS_SEPARATOR_CHARACTER = ','
        self.VLAN_BUSY_CODE = 1
        self.VLAN_FREE_CODE = 0
        
        # Profile Graph
        self.ProfileGraph = NetManager.__ProfileGraph()

        # ovsdb
        self.ovsdb = OvsdbManager(self)

    def init_ovsdb(self):
        self.ovsdb.activate_ovsdbrest()
        self.ovsdb.configure_ovsdbrest()

    class __ProfileGraph(object):
        def __init__(self):
            self.__nffg_endpoints = {}
            self.__nffg_flowrules = {}
            self.__nffg_vnfs = {}
    
        def addEndpoint(self, ep):
            self.__nffg_endpoints[ep.id] = ep
        
        def addFlowrule(self, fr):
            self.__nffg_flowrules[fr.id] = fr

        def addVnf(self, vnf):
            self.__nffg_vnfs[vnf.id] = vnf
        
        def getEndpoint(self, ep_id):
            """

            :param ep_id:
            :return:
            :rtype: EndPoint
            """
            return self.__nffg_endpoints[ep_id]
        
        def getFlowrules(self):
            return self.__nffg_flowrules.values()

        def getVnfs(self):
            return self.__nffg_vnfs.values()

        def get_ep_flowrules(self):
            ep_flowrules = []
            for flowrule in self.__nffg_flowrules.values():
                has_vnf = False
                if flowrule.match.port_in.split(':')[0] == 'vnf':
                    has_vnf = True
                else:
                    for action in flowrule.actions:
                        if action.output is not None and action.output.split(':')[0] == 'vnf':
                            has_vnf = True
                            break
                if not has_vnf:
                    ep_flowrules.append(flowrule)
            return ep_flowrules

        def get_detached_vnfs(self):
            detached_vnfs = []
            for vnf in self.__nffg_vnfs.values():
                is_detached = True
                for flow_from in self.get_flows_from_vnf(vnf):
                    if is_detached:
                        for action in flow_from.actions:
                            if action.output is not action.output.split(':')[0] == 'vnf':
                                is_detached = False
                                break
                if not is_detached:
                    break
                for flow_to in self.get_flows_to_vnf(vnf):
                    if flow_to.match.port_in.split(':')[0] == 'vnf':
                        is_detached = False
                        break
                if is_detached:
                    detached_vnfs.append(vnf)
            return detached_vnfs

        def get_attached_vnfs(self):
            attached_vnfs = []
            for vnf in self.__nffg_vnfs.values():
                is_attached = False
                for flow_from in self.get_flows_from_vnf(vnf):
                    if not is_attached:
                        for action in flow_from.actions:
                            if action.output is not action.output.split(':')[0] == 'vnf':
                                is_attached = True
                                break
                if is_attached:
                    attached_vnfs.append(vnf)
                    break
                for flow_to in self.get_flows_to_vnf(vnf):
                    if flow_to.match.port_in.split(':')[0] == 'vnf':
                        is_attached = True
                        break
                if is_attached:
                    attached_vnfs.append(vnf)
            return attached_vnfs

        def is_detached(self, vnf):
            detached_vnfs = self.get_detached_vnfs()
            return vnf in detached_vnfs

        def get_flows_from_vnf(self, vnf):
            """

            :param vnf:
            :return:
            :rtype: list of Flow
            """
            flow_rules = []
            for port in vnf.ports:
                flow_rules = flow_rules + self.__get_flows_from_node("vnf:"+vnf.id+":"+port.id)
            return flow_rules
            pass

        def get_flows_to_vnf(self, vnf):
            flow_rules = []
            for port in vnf.ports:
                flow_rules = flow_rules + self.__get_flows_to_node("vnf:"+vnf.id+":"+port.id)
            return flow_rules
            pass

        def __get_flows_from_node(self, node_id):
            flow_rules = []
            for flow_rule in self.__nffg_flowrules.values():
                if flow_rule.match.port_in == node_id:
                    flow_rules.append(flow_rule)
            return flow_rules

        def __get_flows_to_node(self, node_id):
            flow_rules = []
            for flow_rule in self.__nffg_flowrules.values():
                for action in flow_rule.actions:
                    if action.output is not action.output == node_id:
                        flow_rules.append(flow_rule)
                        continue
            return flow_rules

    def ProfileGraph_BuildFromNFFG(self, nffg):
        """
        Create a ProfileGraph with the flowrules and endpoints specified in nffg.
        :type nffg: NF_FG
        """
        self.nffg_id = nffg.id

        for endpoint in nffg.end_points:
            if endpoint.status is None:
                endpoint.status = 'new'
            self.ProfileGraph.addEndpoint(endpoint)
        
        for flowrule in nffg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            self.ProfileGraph.addFlowrule(flowrule)

        for vnf in nffg.vnfs:
            if vnf.status is None:
                vnf.status = 'new'
            self.ProfileGraph.addVnf(vnf)
    
    def getControllerName(self):
        if self.isODL():
            return Configuration().CONTROLLER_NAME+" "+Configuration().ODL_VERSION
        elif self.isONOS():
            return Configuration().CONTROLLER_NAME+" "+Configuration().ONOS_VERSION
        else:
            return "<controller unknown>"
    
    def isODL(self):
        return self.ct_name == "OpenDayLight"
    
    def isONOS(self):
        return self.ct_name == "ONOS"
    
    def isODL_Hydrogen(self):
        return self.ct_name == "OpenDayLight" and self.ct_version == "Hydrogen"

    def createFlow(self, efr):
        if self.isODL():
            flowj = Flow("flowrule", efr.get_flow_name(), 0, efr.get_priority(), True, 0, 0, efr.get_actions(), efr.get_match())
            json_req = flowj.getJSON(self.ct_version, efr.get_switch_id())
            ODL_Rest(self.ct_version).createFlow(self.ct_endpoint, self.ct_username, self.ct_password, json_req, efr.get_switch_id(), efr.get_flow_name())
            return efr.get_flow_name()
        
        elif self.isONOS():
            flowj = Flow(efr.get_switch_id(), efr.get_priority(), True, 0, efr.get_actions(), efr.get_match())
            json_req = flowj.getJSON()
            flow_id, response = ONOS_Rest(self.ct_version).createFlow(self.ct_endpoint, self.ct_username, self.ct_password, json_req, efr.get_switch_id())
            return flow_id

    def deleteFlow(self, switch_id, flowname):
        if self.isODL():
            ODL_Rest(self.ct_version).deleteFlow(self.ct_endpoint, self.ct_username, self.ct_password, switch_id, flowname)
        
        elif self.isONOS():
            ONOS_Rest(self.ct_version).deleteFlow(self.ct_endpoint, self.ct_username, self.ct_password, switch_id, flowname)
            
    def activate_app(self, app_name):
        if self.isODL():
            # TODO implement ODL application support
            pass

        elif self.isONOS():
            ONOS_Rest(self.ct_version).activateApp(self.ct_endpoint, self.ct_username, self.ct_password, app_name)

    def deactivate_app(self, app_name):
        if self.isODL():
            # TODO implement ODL application support
            pass

        elif self.isONOS():
            ONOS_Rest(self.ct_version).deactivateApp(self.ct_endpoint, self.ct_username, self.ct_password, app_name)

    def push_app_configuration(self, app_name, app_config_dict):

        network_config = {'apps': {}}
        network_config['apps'][app_name] = {}
        network_config['apps'][app_name][app_name.split('.')[-1]] = app_config_dict
        json_config = json.dumps(network_config)

        if self.isODL():
            # TODO implement ODL application support
            pass
        elif self.isONOS():
            ONOS_Rest(self.ct_version).push_config(self.ct_endpoint, self.ct_username, self.ct_password, json_config)

    def is_application_active(self, app_name):
        if self.isODL():
            # TODO implement ODL application support
            pass

        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).get_application_info(self.ct_endpoint, self.ct_username,
                                                                        self.ct_password, app_name)
            info_dict = json.loads(json_data)
            return info_dict["state"] == "ACTIVE"

    # [CAPABILITIES]

    def get_apps_capabilities(self):

        functional_capabilities = []

        if self.isODL():
            # TODO implement ODL application support
            pass

        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).get_applications_capabilities(
                self.ct_endpoint, self.ct_username, self.ct_password
            )
            capabilities_dict = json.loads(json_data)
            capabilities_array = capabilities_dict['functional-capabilities']
            for capability_dict in capabilities_array:
                functional_capability = FunctionalCapability()
                functional_capability.parse_dict(capability_dict)
                functional_capabilities.append(functional_capability)

        return functional_capabilities

    def get_app_capability(self, app_name):

        functional_capability = FunctionalCapability()

        if self.isODL():
            # TODO implement ODL application support
            pass

        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).get_application_capability(
                self.ct_endpoint, self.ct_username, self.ct_password, app_name
            )
            functional_capability.parse_dict(json.loads(json_data))

        return functional_capability
        
    def getSwitchList(self):
        swList = list()
         
        if self.isODL_Hydrogen():
            
            json_data = ODL_Rest(self.ct_version).getControllerNodes(self.ct_endpoint, self.ct_username, self.ct_password)
            nodes = json.loads(json_data)

            for node in nodes["node"]:
                swList.append({'node_id':node["id"]})

        elif self.isODL():
            
            json_data = ODL_Rest(self.ct_version).getTopology(self.ct_endpoint, self.ct_username, self.ct_password)
            tp = json.loads(json_data)
            nodes = tp["network-topology"]["topology"][0]["node"]
            
            for node in nodes:
                swList.append({'node_id':node["node-id"]})
        
        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).getDevices(self.ct_endpoint, self.ct_username, self.ct_password)
            devices_info = json.loads(json_data)
            
            for device_info in devices_info['devices']:
                swList.append({'node_id': device_info["id"]})

        return swList
    
    def getDevicesInfo(self):

        devices = []

        if self.isODL_Hydrogen():
            # TODO implement
            pass
        elif self.isODL():
            # TODO implement
            pass
        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).getDevices(self.ct_endpoint, self.ct_username, self.ct_password)
            devices_info = json.loads(json_data)
            for device_info in devices_info['devices']:
                device = {'node_id': device_info["id"], 'ports': []}
                json_ports = ONOS_Rest(self.ct_version).getDevicePorts(self.ct_endpoint, self.ct_username, self.ct_password, device_info["id"])
                ports = json.loads(json_ports)['ports']
                for port in ports:
                    device['ports'].append({
                        'port_id': port['port'],
                        'interface': port['annotations']['portName']
                    })
                devices.append(device)
        return devices

    def getDeviceInfo(self, device_id):

        device = {}

        if self.isODL_Hydrogen():
            # TODO implement
            pass
        elif self.isODL():
            # TODO implement
            pass
        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).getDevices(self.ct_endpoint, self.ct_username, self.ct_password)
            devices_info = json.loads(json_data)
            for device_info in devices_info['devices']:
                if device_info["id"] == device_id:
                    device = {'node_id': device_info["id"], 'ports': []}
                    json_ports = ONOS_Rest(self.ct_version).getDevicePorts(self.ct_endpoint, self.ct_username, self.ct_password, device_info["id"])
                    ports = json.loads(json_ports)['ports']
                    for port in ports:
                        if port['isEnabled']:
                            device['ports'].append({
                                'port_id': port['port'],
                                'interface': port['annotations']['portName']
                            })
                    return device

    def getSwitchLinksList(self):
        lkList = list()
         
        if self.isODL_Hydrogen():
            
            json_data = ODL_Rest(self.ct_version).getTopology(self.ct_endpoint, self.ct_username, self.ct_password)
            tp = json.loads(json_data)

            for link in tp["edgeProperties"]:
                head = {'node_id':link["edge"]["headNodeConnector"]["node"]["id"],'port_id':link["edge"]["headNodeConnector"]["id"]}
                tail = {'node_id':link["edge"]["tailNodeConnector"]["node"]["id"],'port_id':link["edge"]["tailNodeConnector"]["id"]}
                lkList.append({'head':head,'tail':tail})
    
        elif self.isODL():
            
            json_data = ODL_Rest(self.ct_version).getTopology(self.ct_endpoint, self.ct_username, self.ct_password)
            tp = json.loads(json_data)
            links = tp["network-topology"]["topology"][0]["link"]
            
            for link in links:
                p_in = link["source"]["source-tp"].split(":")
                p_in = p_in[2]
                
                p_out = link["destination"]["dest-tp"].split(":")
                p_out = p_out[2]
                
                head = {'node_id':link["source"]["source-node"],'port_id':p_in}
                tail = {'node_id':link["destination"]["dest-node"],'port_id':p_out}
                lkList.append({'head':head,'tail':tail})
        
        elif self.isONOS():
            json_data = ONOS_Rest(self.ct_version).getLinks(self.ct_endpoint, self.ct_username, self.ct_password)
            links = json.loads(json_data)
            
            for link in links['links']:
                # check if the link is bidirectional
                for link2 in links['links']:
                    if link2["src"]["device"] == link["dst"]["device"]\
                            and link2["dst"]["device"] == link["src"]["device"]\
                            and link2["src"]["port"] == link["dst"]["port"]\
                            and link2["dst"]["port"] == link["src"]["port"]:
                        p_in = link["src"]["port"]
                        p_out = link["dst"]["port"]
                        head = {'node_id':link["src"]["device"],'port_id':p_in}
                        tail = {'node_id':link["dst"]["device"],'port_id':p_out}

                        lkList.append({'head':head,'tail':tail})
                        break
        
        return lkList
    
    
    ####################################################################################################
    
    
    def setTopologyGraph(self, reset=False):
        
        # Check topology cache
        if self.topology is not None and reset==False:
            return
        
        self.topology = nx.DiGraph()
        swList = self.getSwitchList()
        lkList = self.getSwitchLinksList()

        for sw in swList:
            self.topology.add_node(sw['node_id'])
            
        for lk in lkList:
            self.topology.add_edge(lk["head"]["node_id"],
                                   lk["tail"]["node_id"],
                                   {
                                        self.WEIGHT_PROPERTY_NAME:1, 
                                        'from_port':lk["head"]["port_id"],
                                        'to_port':lk["tail"]["port_id"]
                                    })
    
    
    
    def getNetworkTopology(self):
        self.setTopologyGraph(reset=True)
        array = []
        
        for node in self.topology.nodes():
            sw_neighbours = []
            edges = self.topology.edges(node)
        
            for edge in edges:
                port = self.switchPortOut(edge[0], edge[1])
                port_str = "[ "+str(port)+" ]"
                sw_neighbours.append(port_str+" "+edge[1])

            array.append({ "node":node, "neighbours":sw_neighbours  })
        return array
        
    
    
    
    def getShortestPath(self,source_switch_id,target_switch_id):
        self.setTopologyGraph()
        try:
            path = nx.dijkstra_path(self.topology, source_switch_id, target_switch_id, self.WEIGHT_PROPERTY_NAME)
        except nx.NetworkXNoPath:
            path=None
        return path
    
    
    def switchPortIn(self, switch, from_switch):
        # Return the port of "switch" that receives packets from "from_switch"
        if switch is None or from_switch is None:
            return None
        self.setTopologyGraph()
        #print("topology: " + str(self.topology[]))
        return self.topology[switch][from_switch]['from_port']

    
    def switchPortOut(self, switch, to_switch):
        # Return the port of "switch" that sends packets to "to_switch"
        if switch is None or to_switch is None:
            return None
        self.setTopologyGraph()
        return self.topology[switch][to_switch]['from_port']

    def getPortName(self, switch_id, interface):
        if Configuration().USE_INTERFACES_NAMES:
            return self.getPortByInterfaceName(switch_id, interface)
        else:
            return interface

    def getPortByInterfaceName(self, switch_id, interface):
        # return the port id of a switch by the correspondent interface name
        if switch_id is None or interface is None:
            return None
        if not self.isONOS():
            return interface
        device = self.getDeviceInfo(switch_id)
        if device['node_id'] == switch_id:
            for port in device['ports']:
                if port['interface'] == interface:
                    return port['port_id']
        return None

    # [GRE tunnels]

    def add_gre_tunnel(self, device_id, port_name, local_ip, remote_ip, key):
        self.ovsdb.add_gre_tunnel(device_id, port_name, local_ip, remote_ip, key)

    def delete_gre_tunnel(self, device_id, port_name):
        self.ovsdb.delete_gre_tunnel(device_id, port_name)

    # [physical ports]
    def add_port(self, device_id, port_name):
        self.ovsdb.add_port(device_id, port_name)

    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        CLASS - EXTERNAL FLOWRULE
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
        
    class externalFlowrule(object):
        '''
        Class used to store an external flow rule
        that is going to be pushed in the specified switch.
        '''
        def __init__(self,switch_id=None,nffg_match=None,nffg_actions=None,flow_id=None,priority=None,flowname_suffix=None,nffg_flowrule=None):
            self.__switch_id = switch_id
            self.set_flow_id(flow_id)
            self.set_flow_name(flowname_suffix)
            self.__priority = priority
            
            # nffg_match = nffg.Match object
            match = None
            if nffg_match is not None:
                match = Match(nffg_match)
            self.__match = match
            
            # nffg_actions = array of nffg.Action objects
            self.set_actions(nffg_actions)
            
            # nffg_flowrule = nffg.FlowRule object
            # (usually not used, but useful in some cases)
            self.__nffg_flowrule = nffg_flowrule



        # SWITCH
        
        def get_switch_id(self):
            return self.__switch_id

        def set_switch_id(self, value):
            self.__switch_id = value
        
        
        
        # MATCH

        def get_match(self):
            return self.__match

        def set_match(self, nffgmatch):
            self.__match = Match(nffgmatch)
        
        
        
        # ACTIONS
        
        def get_actions(self):
            return self.__actions

        def append_action(self, nffgaction):
            if nffgaction is None:
                return
            new_action = Action(nffgaction)
            self.__actions.append(new_action)

        def set_actions(self, nffgactions):
            self.__actions = []
            if nffgactions is None:
                return
            for a in nffgactions:
                new_action = Action(a)
                self.__actions.append(new_action)
        
        
        
        # PRIORITY

        def get_priority(self):
            return self.__priority

        def set_priority(self, value):
            self.__priority = value
        
        
        
        # FLOW ID

        def get_flow_id(self):
            return self.__flow_id

        def set_flow_id(self, value):
            self.__flow_id = value
            self.__reset_flow_name()
            
        
        
        # FLOW NAME

        def get_flow_name(self):
            return self.__flow_name
        
        def __reset_flow_name(self):
            self.__flow_name = str(self.__flow_id)+"_"

        def set_flow_name(self, suffix):
            self.__reset_flow_name()
            self.__flow_name_suffix = None
            if(suffix is not None and str(suffix).isdigit()):
                self.__flow_name = self.__flow_name + str(suffix)
                self.__flow_name_suffix = int(suffix)        

        def set_complete_flow_name(self, flow_name):
            fn = self.split_flow_name(flow_name)
            if len(fn)<2:
                return
            self.__flow_id = fn[0]
            self.set_flow_name(fn[1])

        def split_flow_name(self, flow_name=None):
            if flow_name is not None:
                fn = flow_name.split("_")
                if len(fn)<2:
                    return None
                if fn[1].isdigit()==False:
                    return None
                fn[1]=int(fn[1])
                return fn
            return [self.__flow_id,self.__flow_name_suffix]
        
        def inc_flow_name(self):
            fn = self.split_flow_name()
            if fn is not None:
                self.set_flow_name(int(fn[1])+1)
        
        def compare_flow_name(self, flow_name):
            fn1 = self.split_flow_name()
            if fn1 is None:
                return 0
            fn2 = self.split_flow_name(flow_name)
            if fn2 is None:
                return 0
            fn1[1] = int(fn1[1])
            fn2[1] = int(fn2[1])
            return ( fn1[1] - fn2[1] )
            
            

        def setInOut(self, switch_id, action, port_in, port_out, flowname_suffix):
            if(self.__match is None):
                self.__match = Match()
            new_act = Action(action)
            if(port_out is not None):
                new_act.setOutputAction(port_out, 65535)
            
            self.__actions.append(new_act)
            self.__match.setInputMatch(port_in)
            self.__switch_id = switch_id
            self.__flow_name = self.__flow_name+flowname_suffix

        
        def isReady(self):
            return ( self.__switch_id is not None and self.__flow_id is not None )
        
        
        def getNffgMatch(self):
            return self.__match.getNffgMatch(self.__nffg_flowrule)
            

        def getNffgAction(self):
            base_action = Action()
            return base_action.getNffgAction(self.__actions, self.__nffg_flowrule)

'''
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    CLASS - OVSDBREST
* * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
'''


class OvsdbManager(object):

    def __init__(self, net_manager):
        self.net_manager = net_manager
        self.ovsdb_ip = Configuration().OVSDB_IP

    def activate_ovsdbrest(self):

        if self.net_manager.isODL():
            # TODO activate here ODL ovsdbrest API
            pass
        elif self.net_manager.isONOS():
            self.net_manager.activate_app('org.onosproject.ovsdbrest')

    def is_ovsdbrest_running(self):

        if self.net_manager.isODL():
            # TODO check here ODL ovsdbrest API
            pass
        elif self.net_manager.isONOS():
            try:
                ONOS_Rest(self.net_manager.ct_version).check_ovsdbrest(self.net_manager.ct_endpoint,
                                                                       self.net_manager.ct_username,
                                                                       self.net_manager.ct_password)
                return True
            except Exception:
                return False

    def configure_ovsdbrest(self):

        if self.net_manager.isODL():
            # TODO configure ODL ovsdb rest API
            pass
        elif self.net_manager.isONOS():
            config_dict = {
                'nodes': [{'ovsdbIp': Configuration().OVSDB_NODE_IP, 'ovsdbPort': Configuration().OVSDB_NODE_PORT}]
            }
            self.net_manager.push_app_configuration('org.onosproject.ovsdbrest', config_dict)

    def add_port(self, device_id, port_name):

        if self.net_manager.isODL():
            # TODO call ODL ovsdb rest API here
            pass
        elif self.net_manager.isONOS():
            ONOS_Rest(self.net_manager.ct_version)\
                .add_port(self.net_manager.ct_endpoint, self.net_manager.ct_username,
                          self.net_manager.ct_password, self.ovsdb_ip, device_id, port_name)

    def add_gre_tunnel(self, device_id, port_name, local_ip, remote_ip, key):

        if self.net_manager.isODL():
            # TODO call ODL ovsdb rest API here
            pass
        elif self.net_manager.isONOS():
            ONOS_Rest(self.net_manager.ct_version)\
                .add_gre_tunnel(self.net_manager.ct_endpoint, self.net_manager.ct_username,
                                self.net_manager.ct_password, self.ovsdb_ip, device_id, port_name,
                                local_ip, remote_ip, key)

    def delete_gre_tunnel(self, device_id, port_name):

        if self.net_manager.isODL():
            # TODO call ODL ovsdb rest API here
            pass
        elif self.net_manager.isONOS():
            ONOS_Rest(self.net_manager.ct_version)\
                .delete_gre_tunnel(self.net_manager.ct_endpoint, self.net_manager.ct_username,
                                   self.net_manager.ct_password, self.ovsdb_ip, device_id, port_name)
