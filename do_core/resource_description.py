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
        
        # Read default free vlan
        self.__config_vlan_available_ids = self.__set_available_vlan_ids_array(Configuration().VLAN_AVAILABLE_IDS)
        
        self.__readEndpointsAndVlans()
    
    
    
    def updateAll(self):
        for endpoint_name in self.__endpoints:
            
            query = GraphSession().getVlanInIDs(self.__endpoints[endpoint_name]['port'], 
                                                self.__endpoints[endpoint_name]['switch'])
            
            self.__endpoints[endpoint_name]['config']['enabled'] = True
            busy_vlan_ids = []
            
            for q in query:
                
                # If the endpoint has an ingress vlan, add the vlan id to the 'trunk-vlan' array
                if q.vlan_in is not None:
                    busy_vlan_ids.append(int(q.vlan_in))
                    
                # If the endpoint has not an ingress vlan, disable the endpoint
                else:
                    self.__endpoints[endpoint_name]['config']['enabled'] = False
            ''' 
                ep['trunk_vlans_pointer'] has the reference to list object "trunk-vlans" inside self.__dict.
                Every modification on ep['trunk_vlans_pointer'] will affect the list object "trunk-vlans".
            '''
            new_free_vlan_ids = self.__filter_free_vlan_ids(busy_vlan_ids)
            self.__endpoints[endpoint_name]['free_vlans'].clear()
            self.__endpoints[endpoint_name]['free_vlans'].extend(new_free_vlan_ids)
            
            # Update trunk-vlan list
            self.__set_trunk_vlan_list(self.__endpoints[endpoint_name]['trunk_vlans_pointer'],self.__endpoints[endpoint_name]['free_vlans'])
            
    
    
    
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
        
        update_needed = False
        self.__endpoints = {}
        
        for interface in self.__dict["netgroup-domain:informations"]["netgroup-network-manager:informations"]["openconfig-interfaces:interfaces"]["openconfig-interfaces:interface"]:
            name_split = interface['name'].split(self.__endpoint_name_separator)
            if len(name_split)<2:
                continue

            ep = {}
            ep['switch'] = name_split[0]
            ep['port'] = name_split[1]
            ep['free_vlans'] = []
            ep['trunk_vlans_pointer'] = None #reference
            ep['config'] = interface["config"] #reference
            
            interface_vlan = interface["openconfig-if-ethernet:ethernet"]["openconfig-vlan:vlan"]["openconfig-vlan:config"]
            if interface_vlan["interface-mode"] == "TRUNK":
                if "trunk-vlans" not in interface_vlan:
                    interface_vlan["trunk-vlans"] = []
                ep['trunk_vlans_pointer'] = interface_vlan["trunk-vlans"] #reference
                ''' 
                    ep['trunk_vlans_pointer'] has the reference to list object "trunk-vlans" inside self.__dict.
                    Every modification on ep['trunk_vlans_pointer'] will affect the list object "trunk-vlans".
                '''
                if len(ep['trunk_vlans_pointer'])==0:
                    update_needed=True
                    ep['trunk_vlans_pointer'].clear()
                    ep['free_vlans'].clear()
                    ep['free_vlans'].extend(self.__config_vlan_available_ids)
                    self.__set_trunk_vlan_list(ep['trunk_vlans_pointer'],ep['free_vlans'])
                
                else:
                    ep['free_vlans'].extend(self.__set_available_vlan_ids_array(ep['trunk_vlans_pointer']))
            
            self.__endpoints[interface['name']] = ep
        
        # Works only at first use/start of the DO
        if update_needed==True:
            self.saveFile()
    
    
    
    def __set_available_vlan_ids_array(self, vid_ranges):
        
        '''
        Expected vid_ranges = "280..289,90..95,18,31,290..299,52,67..82"
        '''
        
        def __getKey(item):
            return item[0]
        
        vid_array = []
        if isinstance(vid_ranges, str):
            ranges = vid_ranges.split(",")
        else:
            ranges = vid_ranges
            
        for r in ranges:
            r = str(r)
            exs = r.split("..")
            if len(exs)==1:
                exs.append(exs[0])
            elif len(exs)!=2:
                continue
            
            min_vlan_id = int(exs[0])
            max_vlan_id = int(exs[1])
            if (min_vlan_id > max_vlan_id):
                continue
            
            vid_array.append([min_vlan_id,max_vlan_id])
            logging.debug("[CONFIG] - Available VLAN ID - Range: '"+r+"'")
        
        if len(vid_array)==0:
            logging.error("[CONFIG] - VLAN ID - No available vlan id read from '"+vid_ranges+"'")
            return []
        else:
            return sorted(vid_array,key=__getKey)



    def __set_available_vlan_ids_array2(self, vid_ranges):
        
        '''
        Expected vid_ranges = "280-289;90-95;290-299;13-56;57-82;2-5;"
        '''
        
        def __getKey(item):
            return item[0]
        
        vid_array = []
        
        ranges = vid_ranges.split(";")
        for r in ranges:
            exs = r.split("-")
            if len(exs)!=2:
                continue
            
            min_vlan_id = int(exs[0])
            max_vlan_id = int(exs[1])
            if (min_vlan_id > max_vlan_id):
                continue
            
            vid_array.append([min_vlan_id,max_vlan_id])
            logging.debug("[CONFIG] - Available VLAN ID - Range: '"+r+"'")
        
        if len(vid_array)==0:
            logging.error("[CONFIG] - VLAN ID - No available vlan id read from '"+vid_ranges+"'")
            return []
        else:
            return sorted(vid_array,key=__getKey)
    
    
    
    def __filter_free_vlan_ids(self, busy_ids):
        def __getKey(item):
            return item[0]
        
        free_ids = list(self.__config_vlan_available_ids)
        
        for bvid in busy_ids:
            i=0
            for fvid in free_ids:
                
                if bvid>=fvid[0] and bvid<=fvid[1]:
                    
                    if fvid[0]==fvid[1]:
                        free_ids.pop(i)
                    elif bvid==fvid[0]:
                        fvid[0] = fvid[0]+1
                    elif bvid==fvid[1]:
                        fvid[1] = fvid[1]-1
                    else:
                        free_ids.pop(i)
                        free_ids.append([fvid[0],bvid-1])
                        free_ids.append([bvid+1,fvid[1]])
                    break
                i=i+1
        
        free_ids = sorted(free_ids,key=__getKey)
        return free_ids
    
    
    def __set_trunk_vlan_list(self, trunk_vlans_list, free_vlans_list):
        
        trunk_vlans_list.clear()
        
        for fvid in free_vlans_list:
            if fvid[0]==fvid[1]:
                trunk_vlans_list.append(int(fvid[0]))
            else:
                trunk_vlans_list.append(str(fvid[0])+".."+str(fvid[1]))
    
    
    def __set_available_vlan_ids_strings(self, free_ids):
        
        free_ids_string = ""
        for fvid in free_ids:
            if fvid[0]==fvid[1]:
                free_ids_string = free_ids_string+str(fvid[0])+";"
            else:
                free_ids_string = free_ids_string+str(fvid[0])+"-"+str(fvid[1])+";"
        return free_ids_string[:-1]
    
        
    
    
    
    
    
    def checkEndpoint(self, switch, port):
        ep_name = switch+self.__endpoint_name_separator+port
        if ep_name not in self.__endpoints:
            return False
        return True
    
    
    def VlanID_isAvailable(self, vlan_id, switch_id=None, port_id=None):
        if switch_id is None or port_id is None:
            free_vlan_ids = self.__config_vlan_available_ids
        else:
            endpoint_name = switch_id+self.__endpoint_name_separator+port_id
            free_vlan_ids = self.__endpoints[endpoint_name]['free_vlans']
            
        for r in free_vlan_ids:
            if vlan_id>=r[0] and vlan_id<=r[1]:
                return True
        return False
    
    
    def VlanID_getFirstAvailableID(self, switch_id=None, port_id=None):
        if switch_id is None or port_id is None:
            free_vlan_ids = self.__config_vlan_available_ids
        else:
            endpoint_name = switch_id+self.__endpoint_name_separator+port_id
            free_vlan_ids = self.__endpoints[endpoint_name]['free_vlans']
            
        if len(free_vlan_ids)==0 or len(free_vlan_ids)<2:
            return None
        return free_vlan_ids[0][0]
    
    
    def VlanID_getLastAvailableID(self, switch_id=None, port_id=None):
        if switch_id is None or port_id is None:
            free_vlan_ids = self.__config_vlan_available_ids
        else:
            endpoint_name = switch_id+self.__endpoint_name_separator+port_id
            free_vlan_ids = self.__endpoints[endpoint_name]['free_vlans']
            
        if len(free_vlan_ids)==0:
            return None
        last_index = len(free_vlan_ids)-1
        if len(free_vlan_ids)<2:
            return None
        return free_vlan_ids[last_index][1]
    
    
    def VlanID_getAnAvailableID(self, busy_list, switch_id=None, port_id=None):
        if switch_id is None or port_id is None:
            free_vlan_ids = self.__config_vlan_available_ids
        else:
            endpoint_name = switch_id+self.__endpoint_name_separator+port_id
            free_vlan_ids = self.__endpoints[endpoint_name]['free_vlans']
        
        i = 0
        while i<len(free_vlan_ids):
            j = free_vlan_ids[i][0]
            if free_vlan_ids[i][0]==free_vlan_ids[i][1]:
                jlen = 1
            else:
                jlen = free_vlan_ids[i][1]
            while j<=jlen:
                if j not in busy_list:
                    return j
                j=j+1
            i=i+1
        return 0
    
    

ResourceDescription().loadFile(Configuration().MSG_RESDESC_FILE)