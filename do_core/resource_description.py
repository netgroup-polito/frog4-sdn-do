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
    
    
    
    def updateAll(self):
        for endpoint_name in self.__endpoints:
            
            __tvlist = self.__endpoints[endpoint_name]['__trunk_vlans']
            __tvlist.clear()
            for tv in self.__endpoints[endpoint_name]['trunk_vlans']:
                if tv[0]==tv[1]:
                    __tvlist.append(tv[0])
                elif tv[0]<tv[1]:
                    __tvlist.append(str(tv[0])+".."+str(tv[1]))
    
    
    
    def saveFile(self):
        '''
        To print a json file with the original order of keys,
        load the json into a OrderedDict (that stores the original order)
        and we dump the json without sorting the keys (sort_keys=False).
        '''
        output_json = json.dumps(self.__dict,sort_keys=False,indent=2)
        out_file = open(self.__filename,"w")
        out_file.write(output_json)
    
    
    

    def new_flowrule(self, fr_internal_id):
        '''
        Execute some update operations when a new flowrule is added.
            1) TRUNK VLAN: remove a busy vlan id from the endpoint 'trunk-vlan' field
            2) DISABLE ENDPOINT: set the endpoint as 'disabled' when has a match that does not specify a vlan_id 
        '''
        
        fr = GraphSession().getFlowruleByInternalID(fr_internal_id)
        if fr is None:
            return
        match = GraphSession().getMatchByFlowruleID(fr.id)
        if match is None:
            return
        
        if self.checkEndpoint(fr.switch_id, match.port_in)==False:
            return

        # ( 1 ) REMOVE TRUNK VLAN
        if match.vlan_id is not None:
            self.__remove_trunk_vlan(fr.switch_id, match.port_in, match.vlan_id)
        
        # ( 2 ) DISABLE ENDPOINT
        else:
            self.__disable_endpoint(fr.switch_id, match.port_in)
    
    
    
    
    def delete_flowrule(self, fr_internal_id):
        '''
        Execute some update operations when a flowrule is removed.
            1) TRUNK VLAN: add a free vlan id into the endpoint 'trunk-vlan' field
            2) ENABLE ENDPOINT: set the endpoint as 'enabled'
        '''
        
        fr = GraphSession().getFlowruleByInternalID(fr_internal_id)
        if fr is None:
            return
        match = GraphSession().getMatchByFlowruleID(fr.id)
        if match is None:
            return
        
        if self.checkEndpoint(fr.switch_id, match.port_in)==False:
            return
                
        # ( 1 ) ADD TRUNK VLAN
        if match.vlan_id is not None:
            self.__add_trunk_vlan(fr.switch_id, match.port_in, match.vlan_id)
        
        # ( 2 ) ENABLE ENDPOINT
        else:
            self.__enable_endpoint(fr.switch_id, match.port_in)
                    
        

        
    
        
    
    
    def __readEndpointsAndVlans(self):
        
        self.__endpoints = {}
        
        for interface in self.__dict["netgroup-domain:informations"]["netgroup-network-manager:informations"]["openconfig-interfaces:interfaces"]["openconfig-interfaces:interface"]:
            name_split = interface['name'].split(self.__endpoint_name_separator)
            if len(name_split)<2:
                continue
            
            interface_vlan = interface["openconfig-if-ethernet:ethernet"]["openconfig-vlan:vlan"]["openconfig-vlan:config"]

            ep = {}
            ep['switch'] = name_split[0]
            ep['port'] = name_split[1]
            ep['enabled'] = interface['config']['enabled']
            ep['trunk_vlans'] = None
            ep['__trunk_vlans'] = interface_vlan["trunk-vlans"]
            
            if interface_vlan["interface-mode"] == "TRUNK":
                if "trunk-vlans" not in interface_vlan:
                    continue
                ep['trunk_vlans'] = self.__set_trunk_vlan_list(interface_vlan["trunk-vlans"])
                self.__endpoints[interface['name']] = ep
    
    
    
    def __add_trunk_vlan(self, switch_id, port_in, vlan_id):
        
        def getKey(item):
            return item[0]
        
        vlan_id = int(vlan_id)
        epname = switch_id+self.__endpoint_name_separator+port_in
        
        trunk_vlans = self.__endpoints[epname]['trunk_vlans']
        
        i = -1
        for tv in trunk_vlans:
            i = i+1
            
            # add an outermost value
            if (tv[0]-1)==vlan_id or (tv[1]+1)==vlan_id:
                if (tv[0]-1)==vlan_id:
                    tv[0] = tv[0]-1
                
                if (tv[1]+1)==vlan_id:
                    tv[1] = tv[1]+1

                return
            
        # add a single value
        trunk_vlans.append([vlan_id,vlan_id])
        trunk_vlans = sorted(trunk_vlans, key=getKey)
        return
            
        
    
    
    def __remove_trunk_vlan(self, switch_id, port_in, vlan_id):
        
        def getKey(item):
            return item[0]
        
        vlan_id = int(vlan_id)
        epname = switch_id+self.__endpoint_name_separator+port_in
        
        trunk_vlans = self.__endpoints[epname]['trunk_vlans']
        #self.__endpoints[epname]
        
        i = -1
        for tv in trunk_vlans:
            i = i+1
            
            # remove an outermost value
            if tv[0]==vlan_id or tv[1]==vlan_id:
                if tv[0]==vlan_id:
                    tv[0] = tv[0]+1
                
                if tv[1]==vlan_id:
                    tv[1] = tv[1]-1
                
                if tv[0]>tv[1]:
                    trunk_vlans.pop(i)
                return
            
            # remove an inner value
            if tv[0]<vlan_id and tv[1]>vlan_id:
                trunk_vlans.append([tv[0],vlan_id-1])
                trunk_vlans.append([vlan_id+1,tv[1]])
                trunk_vlans.pop(i)
                trunk_vlans = sorted(trunk_vlans, key=getKey)
                return
    
    
    
    def __enable_endpoint(self, switch_id, port_in):
        
        epname = switch_id+self.__endpoint_name_separator+port_in
        trunk_vlans = self.__endpoints[epname]['enabled'] = True
        
        
        
    def __disable_endpoint(self, switch_id, port_in):
        
        epname = switch_id+self.__endpoint_name_separator+port_in
        trunk_vlans = self.__endpoints[epname]['enabled'] = False
            
            
            
            
        
        
        
        
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
                trunk_vlans.append(str(r[0])+".."+str(r[1]))
                trunk_vlans = trunk_vlans+str(r[0])+"-"+str(r[1])+";"
            else:
                trunk_vlans = trunk_vlans+str(r[0])+";"
        return trunk_vlans[:-1]
    
    

ResourceDescription().loadFile(Configuration().MSG_RESDESC_FILE)