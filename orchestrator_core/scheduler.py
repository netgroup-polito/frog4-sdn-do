'''
Created on Oct 1, 2014

@author: fabiomignini
'''

from orchestrator_core.component_adapter.OpenDayLight_CA.controller import OpenDayLight_CA
from orchestrator_core.exception import NodeNotFound
from orchestrator_core.sql.node import Node
from orchestrator_core.sql.graph import Graph

import logging

class Scheduler(object):
    
    def __init__(self, graph_id, userdata):
        self.graph_id = graph_id
        self.userdata = userdata
    
    def schedule(self, nffg):      
        node = Node().getNodeFromDomainID(self.checkEndpointLocation(nffg))
        self.changeAvailabilityZone(nffg, Node().getAvailabilityZone(node.id))
        
        orchestratorCA_instance = self.getInstance(node)
        return orchestratorCA_instance, node
        
    def getInstance(self, node):
        if node.type == "ODL":
            orchestratorCA_instance = OpenDayLight_CA(self.graph_id, self.userdata)
        else:
            logging.error("Driver not supported: "+node.type)
            raise
        return orchestratorCA_instance

    def changeAvailabilityZone(self, nffg, availability_zone):
        for vnf in nffg.vnfs:
            vnf.availability_zone = availability_zone
    
    def checkEndpointLocation(self, nffg):
        '''
        Define the node where to instantiate the nffg
        '''
        node = None
        for end_point in nffg.end_points:
            if end_point.node is not None:
                node = end_point.node
                break
            elif end_point.switch_id is not None:
                node = end_point.switch_id
                break
        if node is None:
            raise NodeNotFound("Unable to determine where to place this graph (endpoint.node or endpoint.switch_id missing)")
        return node
