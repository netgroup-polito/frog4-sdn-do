import json
from collections import OrderedDict
from odl_do.config import Configuration
from odl_do.sql.graph_session import GraphSession

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
    
    
    def saveFile(self):
        '''
        To print a json file with the original order of keys,
        load the json into a OrderedDict (that stores the original order)
        and we dump the json without sorting the keys (sort_keys=False).
        '''
        output_json = json.dumps(self.__dict,sort_keys=False,indent=2)
        out_file = open(self.__filename,"w")
        out_file.write(output_json)
        
        
    
    def __readEndpointsAndVlans(self):
        
        self.__endpoints = {}
        
        for interface in self.__dict["netgroup-domain:informations"]["netgroup-network-manager:informations"]["openconfig-interfaces:interfaces"]["openconfig-interfaces:interface"]:
            name_split = interface['name'].split(self.__endpoint_name_separator)
            if len(name_split)<2:
                continue
            
            ep = {}
            ep['switch'] = name_split[0]
            ep['port'] = name_split[1]
            ep['busy_vlans'] = []
            
            interface_vlan = interface["openconfig-if-ethernet:ethernet"]["openconfig-vlan:vlan"]["openconfig-vlan:config"]
            if interface_vlan["interface-mode"] == "TRUNK":
                if "trunk-vlans" not in interface_vlan:
                    interface_vlan["trunk-vlans"] = []
                ep['busy_vlans'] = interface_vlan["trunk-vlans"] #reference
                ''' 
                    ep['busy_vlans'] has the reference to list object "trunk-vlans" inside self.__dict.
                    Every modification on ep['busy_vlans'] will affect the list object "trunk-vlans".
                '''
            self.__endpoints[interface['name']] = ep
    
    
    
    def updateTrunkVlanIDs(self):
        for endpoint_name in self.__endpoints:
            
            query = GraphSession().getVlanInIDs(self.__endpoints[endpoint_name]['port'], 
                                                self.__endpoints[endpoint_name]['switch'])
            
            self.__endpoints[endpoint_name]['busy_vlans'].clear()
            
            for q in query:
                self.__endpoints[endpoint_name]['busy_vlans'].append(int(q.vlan_in))

            ''' 
                ep['busy_vlans'] has the reference to list object "trunk-vlans" inside self.__dict.
                Every modification on ep['busy_vlans'] will affect the list object "trunk-vlans".
            '''
    
    
    def checkEndpoint(self, switch, port):
        ep_name = switch+self.__endpoint_name_separator+port
        if ep_name not in self.__endpoints:
            return False
        return True
    
    

ResourceDescription().loadFile(Configuration().MSG_RESDESC_FILE)