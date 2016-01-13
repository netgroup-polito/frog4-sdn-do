'''
Created on Nov 10, 2015

@author: giacomo
'''

#TODO: import logging

import json
import networkx as nx
#from networkx.readwrite import json_graph

from odl_do.odl_rest import ODL_Rest


class NetGraph():


    def __init__(self, odlversion, odlendpoint, odlusername, odlpassword):
        
        self.odlendpoint = odlendpoint
        self.odlusername = odlusername
        self.odlpassword = odlpassword
        self.odlversion = odlversion
        
        self.topology = None #nx.Graph()
        self.WEIGHT_PROPERTY_NAME = 'weight'
        self.ACTIONS_SEPARATOR_CHARACTER = ','
        self.VLAN_BUSY_CODE = 1
        self.VLAN_FREE_CODE = 0
        
        
    def print_json(self,data):
        print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))        
        
        
    def getSwitchList(self):
        swList = list()
         
        if self.odlversion == "Hydrogen":
            
            json_data = ODL_Rest(self.odlversion).getControllerNodes(self.odlendpoint, self.odlusername, self.odlpassword)
            nodes = json.loads(json_data)

            for node in nodes["node"]:
                swList.append({'node_id':node["id"]})

        else:
            json_data = ODL_Rest(self.odlversion).getTopology(self.odlendpoint, self.odlusername, self.odlpassword)
            tp = json.loads(json_data)
            nodes = tp["network-topology"]["topology"][0]["node"]
            
            for node in nodes:
                swList.append({'node_id':node["node-id"]})
        
        return swList
    
    
    
    def getSwitchLinksList(self):
        lkList = list()
         
        if self.odlversion == "Hydrogen":
            json_data = ODL_Rest(self.odlversion).getTopology(self.odlendpoint, self.odlusername, self.odlpassword)
            tp = json.loads(json_data)

            for link in tp["edgeProperties"]:
                head = {'node_id':link["edge"]["headNodeConnector"]["node"]["id"],'port_id':link["edge"]["headNodeConnector"]["id"]}
                tail = {'node_id':link["edge"]["tailNodeConnector"]["node"]["id"],'port_id':link["edge"]["tailNodeConnector"]["id"]}
                lkList.append({'head':head,'tail':tail})

        else:
            json_data = ODL_Rest(self.odlversion).getTopology(self.odlendpoint, self.odlusername, self.odlpassword)
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
        
        return lkList
    
    
    
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
        return self.topology[switch][from_switch]['from_port']
    
    def switchPortOut(self, switch, to_switch):
        # Return the port of "switch" that sends packets to "to_switch"
        if switch is None or to_switch is None:
            return None
        self.setTopologyGraph()
        return self.topology[switch][to_switch]['from_port']
