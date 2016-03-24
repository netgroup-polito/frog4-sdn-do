import json, logging
from collections import OrderedDict
from do_core.config import Configuration
from do_core.sql.graph_session import GraphSession

class ResourceDescription(object):  # Singleton Class
    
    __filename = None
    __dict = None
    __endpoint_name_separator = "/"
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ResourceDescription, cls).__new__(cls, *args, **kwargs)
        return cls._instance 
    
    
    def __init__(self):
        return
    
    
    def loadFile(self,filename):
        if self.__filename == filename:
            return
        
        self.__filename = filename
        
        in_file = open(self.__filename,"r")
        read = in_file.read()
        self.__dict = json.loads(read,object_hook=OrderedDict,object_pairs_hook=OrderedDict)
        
        # TODO: validate json
        
        self.__readEndpointsAndVlans()
        
    
    
    def __readEndpointsAndVlans(self):
        
        self.__endpoints = {}
        
        for interface in self.__dict["netgroup-domain:informations"]["netgroup-network-manager:informations"]["openconfig-interfaces:interfaces"]["openconfig-interfaces:interface"]:
            name_split = interface['name'].split(self.__endpoint_name_separator)
            if len(name_split)<2:
                continue

            ep = {}
            ep['switch'] = name_split[0]
            ep['port'] = name_split[1]
            ep['enabled'] = interface['config']['enabled']
            ep['trunk_vlans'] = None
            
            interface_vlan = interface["openconfig-if-ethernet:ethernet"]["openconfig-vlan:vlan"]["openconfig-vlan:config"]
            if interface_vlan["interface-mode"] == "TRUNK":
                if "trunk-vlans" not in interface_vlan:
                    continue
                ep['trunk_vlans'] = self.__set_trunk_vlan_list(interface_vlan["trunk-vlans"])
                self.__endpoints[interface['name']] = ep
    
    
    
    def __set_trunk_vlan_list(self, trunk_vlans_list):
        
        newlist = []
        
        for tvid in trunk_vlans_list:
            if isinstance(tvid, str):
                range = tvid.split("..")
                if len(range)==2:
                    range[0] = int(range[0])
                    range[1] = int(range[1])
                    newlist.append(range)
            elif isinstance(tvid, int):
                newlist.append([tvid,tvid])
        
        return newlist
        
    
    
    
    
    
    def checkEndpoint(self, switch, port):
        ep_name = switch+self.__endpoint_name_separator+port
        if ep_name not in self.__endpoints:
            return False
        return True
    
    
    def VlanID_isAvailable(self, vlan_id, switch_id, port_id):
        endpoint_name = switch_id+self.__endpoint_name_separator+port_id 
        for r in self.__endpoints[endpoint_name]['trunk_vlans']:
            if vlan_id>=r[0] and vlan_id<=r[1]:
                return True
        return False
    
    
    def VlanID_getAvailables(self, switch_id, port_id):
        endpoint_name = switch_id+self.__endpoint_name_separator+port_id
        trunk_vlans = []
        for r in self.__endpoints[endpoint_name]['trunk_vlans']:
            if r[0]>r[1]:
                trunk_vlans.append(r[0]+".."+r[1])
            else:
                trunk_vlans.append(r[0])
        return trunk_vlans
    
    
    def VlanID_getAvailables_asString(self, switch_id, port_id):
        endpoint_name = switch_id+self.__endpoint_name_separator+port_id
        trunk_vlans = ""
        for r in self.__endpoints[endpoint_name]['trunk_vlans']:
            if r[0]>r[1]:
                trunk_vlans.append(r[0]+".."+r[1])
                trunk_vlans = trunk_vlans+r[0]+"-"+r[1]+";"
            else:
                trunk_vlans = trunk_vlans+r[0]+";"
        return trunk_vlans[:-1]
    
    

ResourceDescription().loadFile(Configuration().MSG_RESDESC_FILE)