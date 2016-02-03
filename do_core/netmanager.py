'''
Created on Nov 10, 2015

@author: giacomo
'''

import json
import networkx as nx

from do_core.config import Configuration


if Configuration().CONTROLLER_NAME == "OpenDayLight":
    from do_core.odl.objects import Flow, Match ,Action
    from do_core.odl.rest import ODL_Rest
    
elif Configuration().CONTROLLER_NAME == "ONOS":
    from do_core.onos.objects import Flow, Selector as Match, Treatment as Action
    from do_core.onos.rest import ONOS_Rest
        


class NetManager():

    def __init__(self):
        
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
        self.topology = None #nx.Graph()
        self.WEIGHT_PROPERTY_NAME = 'weight'
        self.ACTIONS_SEPARATOR_CHARACTER = ','
        self.VLAN_BUSY_CODE = 1
        self.VLAN_FREE_CODE = 0
        
        # Profile Graph
        self.ProfileGraph = NetManager.__ProfileGraph()
    
    
    class __ProfileGraph(object):
        def __init__(self):
            self.__nffg_endpoints = {}
            self.__nffg_flowrules = {}
    
        def addEndpoint(self, ep):
            self.__nffg_endpoints[ep.id] = ep
        
        def addFlowrule(self, fr):
            self.__nffg_flowrules[fr.id] = fr
        
        def getEndpoint(self, ep_id):
            return self.__nffg_endpoints[ep_id]
        
        def getFlowrules(self):
            return self.__nffg_flowrules.values()
    
    
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
            devices = json.loads(json_data)
            
            for device in devices['devices']:
                swList.append({'node_id':device["id"]})
            
        return swList
    
    
    
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
                p_in = link["src"]["port"]
                p_out = link["dst"]["port"]
                
                head = {'node_id':link["src"]["device"],'port_id':p_in}
                tail = {'node_id':link["dst"]["device"],'port_id':p_out}
                lkList.append({'head':head,'tail':tail})
        
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
        return self.topology[switch][from_switch]['from_port']

    
    def switchPortOut(self, switch, to_switch):
        # Return the port of "switch" that sends packets to "to_switch"
        if switch is None or to_switch is None:
            return None
        self.setTopologyGraph()
        return self.topology[switch][to_switch]['from_port']
