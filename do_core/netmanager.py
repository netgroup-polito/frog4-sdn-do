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

    
    def ProfileGraph_BuildFromNFFG(self, nffg):
        '''
        Create a ProfileGraph with the flowrules and endpoints specified in nffg.
        '''
        for endpoint in nffg.end_points:
            
            if endpoint.status is None:
                endpoint.status = "new"
                
            self.ProfileGraph.addEndpoint(endpoint)
        
        for flowrule in nffg.flow_rules:
            if flowrule.status is None:
                flowrule.status = 'new'
            self.ProfileGraph.addFlowrule(flowrule)
            
            
    
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



