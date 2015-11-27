'''
Created on Nov 10, 2015

@author: giacomo
'''

#TODO: import logging

import json
import networkx as nx
#from networkx.readwrite import json_graph

from odl_ca_core.ODL_Rest import ODL_Rest


class NetGraph():


    def __init__(self, odlversion, odlendpoint, odlusername, odlpassword):
        
        self.odlendpoint = odlendpoint
        self.odlusername = odlusername
        self.odlpassword = odlpassword
        self.odlversion = odlversion
        
        #variables declared by Matteo
        self.topology = nx.Graph();
        self.WEIGHT_PROPERTY_NAME = 'weight'
        self.ACTIONS_SEPARATOR_CHARACTER = ','
        self.VLAN_BUSY_CODE = 1
        self.VLAN_FREE_CODE = 0
        #end of custom variable declaration
        
        
        
    def print_json(self,data):
        print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        
        
        
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
    
    
    
    def getTopologyGraph(self):
        
        print "getTopologyGraph"
        
        myGraph = nx.DiGraph()
        
        swList = self.getSwitchList()
        lkList = self.getSwitchLinksList()
        
        for sw in swList:
            myGraph.add_node(sw['node_id'])
            
        for lk in lkList:
            p_in = lk["head"]["port_id"]
            p_out = lk["tail"]["port_id"]
            
            myGraph.add_edge(lk["head"]["node_id"],lk["tail"]["node_id"],
                             {self.WEIGHT_PROPERTY_NAME:1, 'from_port':p_in,'to_port':p_out})

        self.topology = myGraph
        return myGraph
    
    
    
    def getShortestPath(self,source_switch_id,target_switch_id):
        
        print "getShortestPath"
        
        try:
            path = nx.dijkstra_path(self.topology, source_switch_id, target_switch_id, self.WEIGHT_PROPERTY_NAME)
        except nx.NetworkXNoPath:
            path=None
        return path
    
    
    
    
    
    
    
    
    
    
    
    
    
    