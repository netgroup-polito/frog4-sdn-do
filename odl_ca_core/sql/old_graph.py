'''
Created on Jun 20, 2015

@author: fabiomignini
'''
from exceptions import Exception 
from sqlalchemy import Column, VARCHAR, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from odl_ca_core.sql.sql_server import get_session
from sqlalchemy.sql import func
from sqlalchemy.orm.exc import NoResultFound

from odl_ca_core.config import Configuration
from odl_ca_core.sql.session import Session
import datetime
import logging
from nffg_library.nffg import NF_FG, Port, EndPoint, FlowRule, Match, Action
from odl_ca_core.exception import EndpointNotFound, PortNotFound, GraphNotFound

Base = declarative_base()
sqlserver = Configuration().CONNECTION

class GraphModel(Base):
    '''
    Maps the database table graph
    '''
    __tablename__ = 'graph'
    attributes = ['id', 'session_id','node_id','partial']
    id = Column(Integer, primary_key=True)
    session_id = Column(VARCHAR(64))
    node_id = Column(VARCHAR(64))
    partial = Column(Boolean())
    


class PortModel(Base):
    '''
    Maps the database table node
    '''
    __tablename__ = 'port'
    attributes = ['id', 'internal_id', 'graph_port_id', 'graph_id', 'name','vnf_id', 'location','type', 'virtual_switch', 'status', 'creation_date','last_update', 'os_network_id',
                    'mac_address', 'ipv4_address', 'vlan_id','gre_key']
    id = Column(Integer, primary_key=True)
    internal_id = Column(VARCHAR(64)) # id in the infrastructure
    graph_port_id = Column(VARCHAR(64)) # id in the json
    graph_id = Column(Integer)
    name = Column(VARCHAR(64))
    vnf_id = Column(VARCHAR(64)) # could be NULL, for example a port in an end-point
    location = Column(VARCHAR(64)) # node where the port is instantiated
    type = Column(VARCHAR(64)) # OpenStack port, etc.
    virtual_switch = Column(VARCHAR(64))
    status = Column(VARCHAR(64)) # initialization, complete, error
    creation_date = Column(VARCHAR(64))
    last_update = Column(VARCHAR(64))
    os_network_id = Column(VARCHAR(64))
    mac_address = Column(VARCHAR(64))
    ipv4_address = Column(VARCHAR(64))
    vlan_id = Column(VARCHAR(64))
    gre_key = Column(VARCHAR(64))
    
class EndpointModel(Base):
    '''
    Maps the database table endpoint
    '''
    __tablename__ = 'endpoint'
    attributes = ['id', 'internal_id', 'graph_endpoint_id','graph_id','name', 'type','location']
    id = Column(Integer, primary_key=True)
    internal_id = Column(VARCHAR(64)) # id of the infrastructure graph
    graph_endpoint_id = Column(VARCHAR(64)) # id in the json
    graph_id = Column(VARCHAR(64))
    name = Column(VARCHAR(64))
    type = Column(VARCHAR(64)) # internal, interface, interface-out, vlan, gre
    location = Column(VARCHAR(64)) # node where the end-point is instantiated
    
class EndpointResourceModel(Base):
    '''
    Maps the database table endpoint_resource
    '''
    __tablename__ = 'endpoint_resource'
    attributes = ['endpoint_id', 'resource_type', 'resource_id']
    endpoint_id = Column(Integer, primary_key=True)
    resource_type = Column(VARCHAR(64), primary_key=True) # port or flow-rule (flow-rule will be the flow-rules that connect the end-point to an external end-point)
    resource_id = Column(Integer, primary_key=True)

class FlowRuleModel(Base):
    '''
    Maps the database table node
    '''
    __tablename__ = 'flow_rule'
    attributes = ['id', 'internal_id', 'graph_flow_rule_id', 'graph_id','node_id', 'type', 'priority','status', 'creation_date','last_update']
    id = Column(Integer, primary_key=True)
    internal_id = Column(VARCHAR(64)) # id of the infrastructure graph
    graph_flow_rule_id = Column(VARCHAR(64)) # id in the json
    graph_id = Column(VARCHAR(64))
    node_id = Column(VARCHAR(64))
    type = Column(VARCHAR(64))
    priority = Column(VARCHAR(64)) # openflow priority    
    status = Column(VARCHAR(64)) # initialization, complete, error
    creation_date = Column(VARCHAR(64))
    last_update = Column(VARCHAR(64))
    
class MatchModel(Base):
    '''
    Maps the database table match
    '''
    __tablename__ = 'match'

    attributes = ['id', 'flow_rule_id', 'port_in_type', 'port_in', 'ether_type','vlan_id','vlan_priority', 'source_mac','dest_mac','source_ip',
                 'dest_ip','tos_bits','source_port', 'dest_port', 'protocol']
    id = Column(Integer, primary_key=True)
    flow_rule_id = Column(Integer)
    port_in_type = Column(VARCHAR(64)) # port or endpoint
    port_in = Column(VARCHAR(64))
    ether_type = Column(VARCHAR(64))
    vlan_id = Column(VARCHAR(64))
    vlan_priority = Column(VARCHAR(64))
    source_mac = Column(VARCHAR(64))
    dest_mac = Column(VARCHAR(64))
    source_ip = Column(VARCHAR(64))
    dest_ip = Column(VARCHAR(64))
    tos_bits = Column(VARCHAR(64))
    source_port = Column(VARCHAR(64))
    dest_port = Column(VARCHAR(64))
    protocol = Column(VARCHAR(64))

class ActionModel(Base):
    '''
    Maps the database table action
    '''
    __tablename__ = 'action'

    attributes = ['id', 'flow_rule_id', 'output_type', 'output', 'controller', '_drop', 'set_vlan_id','set_vlan_priority','pop_vlan', 'set_ethernet_src_address',
                  'set_ethernet_dst_address','set_ip_src_address','set_ip_dst_address', 'set_ip_tos','set_l4_src_port','set_l4_dst_port', 'output_to_queue']    
    id = Column(Integer, primary_key=True)
    flow_rule_id = Column(Integer)
    output_type = Column(VARCHAR(64)) # port or endpoint
    output = Column(VARCHAR(64))
    controller = Column(Boolean)
    _drop = Column(Boolean)
    set_vlan_id = Column(VARCHAR(64))
    set_vlan_priority = Column(VARCHAR(64))
    pop_vlan = Column(Boolean)
    set_ethernet_src_address = Column(VARCHAR(64))
    set_ethernet_dst_address = Column(VARCHAR(64))
    set_ip_src_address = Column(VARCHAR(64))
    set_ip_dst_address = Column(VARCHAR(64))
    set_ip_tos = Column(VARCHAR(64))
    set_l4_src_port = Column(VARCHAR(64))
    set_l4_dst_port = Column(VARCHAR(64))
    output_to_queue = Column(VARCHAR(64))


class GraphConnectionModel(Base):
    '''
    Maps the database table graph_connection
    '''
    __tablename__ = 'graph_connection'
    attributes = ['endpoint_id_1', 'endpoint_id_2']
    endpoint_id_1 = Column(VARCHAR(64), primary_key=True)
    endpoint_id_2 = Column(VARCHAR(64), primary_key=True)

    
class Graph(object):
    def __init__(self):
        self.user_session = Session()

    
        
    def addNFFG(self, nffg, session_id, partial=False):
        session = get_session()  
        with session.begin():
            self.id_generator(nffg, session_id)
            graph_ref = GraphModel(id=nffg.db_id, session_id=session_id, partial=partial)
            session.add(graph_ref)
                            
            for flow_rule in nffg.flow_rules:
                
                self.addFlowRule(nffg.db_id, flow_rule, nffg)                
            for endpoint in nffg.end_points:
                endpoint_ref = EndpointModel(id=endpoint.db_id, graph_endpoint_id=endpoint.id, 
                                             graph_id=nffg.db_id, name = endpoint.name, type=endpoint.type)
                session.add(endpoint_ref)
                
                # Add end-point resources
                # End-point attached to something that is not another graph
                if "interface" in endpoint.type or endpoint.type == "vlan":
                    port_ref = PortModel(id=self.port_id, graph_port_id = endpoint.interface, graph_id=nffg.db_id, 
                                         internal_id=endpoint.interface, name=endpoint.interface, location=endpoint.node,
                                         virtual_switch=endpoint.switch_id, vlan_id=endpoint.vlan_id, creation_date=datetime.datetime.now(), 
                                         last_update=datetime.datetime.now())
                    session.add(port_ref)
                    endpoint_resource_ref = EndpointResourceModel(endpoint_id=endpoint.db_id,
                                          resource_type='port',
                                          resource_id=self.port_id)
                    session.add(endpoint_resource_ref)
                    self.port_id = self.port_id + 1
                
                # End-point attached to another graph
                if endpoint.remote_endpoint_id is not None:
                    # TODO: Add graph connection
                    remote_graph_db_id =  endpoint.remote_endpoint_id.split(':')[0]
                    endpoint2_db_id = self._getEndpointID(endpoint.remote_endpoint_id.split(':')[1], remote_graph_db_id)
                    graph_connection_ref = GraphConnectionModel(endpoint_id_1=endpoint.db_id, endpoint_id_2=endpoint2_db_id)
                    session.add(graph_connection_ref)
  
    def addFlowRule(self, graph_id, flow_rule, nffg):
        session = get_session()
        with session.begin():  
            # FlowRule
            if self._get_higher_flow_rule_id() is not None:
                flow_rule_db_id = self._get_higher_flow_rule_id() + 1
            else:
                flow_rule_db_id = 0
            flow_rule_ref = FlowRuleModel(id=flow_rule_db_id, internal_id=flow_rule.internal_id, 
                                       graph_flow_rule_id=flow_rule.id, graph_id=graph_id,
                                       priority=flow_rule.priority,  status=flow_rule.status,
                                       creation_date=datetime.datetime.now(), last_update=datetime.datetime.now(), type=flow_rule.type, node_id=flow_rule.node_id)
            session.add(flow_rule_ref)
            
            # Match
            if flow_rule.match is not None:
                match_db_id = flow_rule_db_id
                port_in_type = None
                port_in = None
                if flow_rule.match.port_in.split(':')[0] == 'endpoint':
                    port_in_type = 'endpoint'
                    port_in = nffg.getEndPoint(flow_rule.match.port_in.split(':')[1]).db_id
                match_ref = MatchModel(id=match_db_id, flow_rule_id=flow_rule_db_id, port_in_type = port_in_type, port_in=port_in,
                                ether_type=flow_rule.match.ether_type, vlan_id=flow_rule.match.vlan_id,
                                vlan_priority=flow_rule.match.vlan_priority, source_mac=flow_rule.match.source_mac,
                                dest_mac=flow_rule.match.dest_mac, source_ip=flow_rule.match.source_ip,
                                dest_ip=flow_rule.match.dest_ip, tos_bits=flow_rule.match.tos_bits,
                                source_port=flow_rule.match.source_port, dest_port=flow_rule.match.dest_port,
                                protocol=flow_rule.match.protocol)
                session.add(match_ref)
            
            # Actions
            if flow_rule.actions:
                if self._get_higher_action_id() is not None:
                    action_db_id = self._get_higher_action_id() + 1
                else:
                    action_db_id = 0
                for action in flow_rule.actions:
                    output_type = None
                    output = None
                    if action.output != None and action.output.split(':')[0] == 'endpoint':
                        output_type = 'endpoint'
                        output = nffg.getEndPoint(action.output.split(':')[1]).db_id
                    action_ref = ActionModel(id=action_db_id, flow_rule_id=flow_rule_db_id,
                                             output_type=output_type, output=output,
                                             controller=action.controller, _drop=action.drop, set_vlan_id=action.set_vlan_id,
                                             set_vlan_priority=action.set_vlan_priority, pop_vlan=action.pop_vlan,
                                             set_ethernet_src_address=action.set_ethernet_src_address, 
                                             set_ethernet_dst_address=action.set_ethernet_dst_address,
                                             set_ip_src_address=action.set_ip_src_address, set_ip_dst_address=action.set_ip_dst_address,
                                             set_ip_tos=action.set_ip_tos, set_l4_src_port=action.set_l4_src_port,
                                             set_l4_dst_port=action.set_l4_dst_port, output_to_queue=action.output_to_queue)
                    session.add(action_ref)
                    action_db_id += 1
                    
    def addFlowRuleAsEndpointResource(self, graph_id, flow_rule, nffg, endpoint_id):
        session = get_session()
        with session.begin():  
            # FlowRule
            if self._get_higher_flow_rule_id() is not None:
                flow_rule_db_id = self._get_higher_flow_rule_id() + 1
            else:
                flow_rule_db_id = 0
            flow_rule_ref = FlowRuleModel(id=flow_rule_db_id, internal_id=flow_rule.internal_id, 
                                       graph_flow_rule_id=flow_rule.id, graph_id=graph_id,
                                       priority=flow_rule.priority,  status=flow_rule.status,
                                       creation_date=datetime.datetime.now(), last_update=datetime.datetime.now(), type=flow_rule.type, node_id=flow_rule.node_id)
            session.add(flow_rule_ref)
            
            # Match
            if flow_rule.match is not None:
                match_db_id = flow_rule_db_id
                port_in_type = None
                port_in = None
                if flow_rule.match.port_in.split(':')[0] == 'endpoint':
                    port_in_type = 'endpoint'
                    port_in = nffg.getEndPoint(flow_rule.match.port_in.split(':')[1]).db_id
                match_ref = MatchModel(id=match_db_id, flow_rule_id=flow_rule_db_id, port_in_type = port_in_type, port_in=port_in,
                                ether_type=flow_rule.match.ether_type, vlan_id=flow_rule.match.vlan_id,
                                vlan_priority=flow_rule.match.vlan_priority, source_mac=flow_rule.match.source_mac,
                                dest_mac=flow_rule.match.dest_mac, source_ip=flow_rule.match.source_ip,
                                dest_ip=flow_rule.match.dest_ip, tos_bits=flow_rule.match.tos_bits,
                                source_port=flow_rule.match.source_port, dest_port=flow_rule.match.dest_port,
                                protocol=flow_rule.match.protocol)
                session.add(match_ref)
            
            # Actions
            if flow_rule.actions:
                if self._get_higher_action_id() is not None:
                    action_db_id = self._get_higher_action_id() + 1
                else:
                    action_db_id = 0
                for action in flow_rule.actions:
                    output_type = None
                    output = None
                    if action.output != None and action.output.split(':')[0] == 'endpoint':
                        output_type = 'endpoint'
                        output = nffg.getEndPoint(action.output.split(':')[1]).db_id
                    action_ref = ActionModel(id=action_db_id, flow_rule_id=flow_rule_db_id,
                                             output_type=output_type, output=output,
                                             controller=action.controller, _drop=action.drop, set_vlan_id=action.set_vlan_id,
                                             set_vlan_priority=action.set_vlan_priority, pop_vlan=action.pop_vlan,
                                             set_ethernet_src_address=action.set_ethernet_src_address, 
                                             set_ethernet_dst_address=action.set_ethernet_dst_address,
                                             set_ip_src_address=action.set_ip_src_address, set_ip_dst_address=action.set_ip_dst_address,
                                             set_ip_tos=action.set_ip_tos, set_l4_src_port=action.set_l4_src_port,
                                             set_l4_dst_port=action.set_l4_dst_port, output_to_queue=action.output_to_queue)
                    session.add(action_ref)
                    action_db_id += 1
                    
            endpoint_resource_ref = EndpointResourceModel(endpoint_id=endpoint_id,
                                                              resource_type='flowrule',
                                                              resource_id=flow_rule_db_id)
            session.add(endpoint_resource_ref)
    
    
    

    
    
        
   
   
   
   
   
    
    

    
    
    
    def getPorts(self, graph_id):
        session = get_session()
        return session.query(PortModel).filter_by(graph_id = graph_id).all()
    
    def setPortInternalID(self, graph_id, vnf_id, port_graph_id, port_internal_id, port_status, port_type):
        session = get_session()
        logging.debug("graph_id: "+str(graph_id)+" vnf_id: "+str(vnf_id)+" port_graph_id: "+str(port_graph_id))
        with session.begin():
            res = session.query(PortModel).filter_by(graph_port_id = port_graph_id).filter_by(vnf_id = vnf_id).filter_by(graph_id = graph_id).update({"internal_id": port_internal_id,"last_update":datetime.datetime.now(), 'status':port_status, 'type':port_type})
            logging.debug("Num of tuple: "+str(res))
            assert (res==1)
            
    def setPortMacAddress(self, port_id, mac_address):
        session = get_session()  
        with session.begin():
            assert (session.query(PortModel).filter_by(id = port_id).update({"mac_address": mac_address,"last_update":datetime.datetime.now()})==1)
    
    def checkMacAddress(self, mac_address):
        session = get_session()  
        with session.begin():
            session.query(PortModel).filter_by(mac_address = mac_address).one()

    def setFlowRuleInternalID(self, graph_id, graph_flow_rule_id, internal_id, status='complete'):
        session = get_session()  
        with session.begin():
            session.query(FlowRuleModel).filter_by(graph_flow_rule_id = graph_flow_rule_id).filter_by(graph_id = graph_id).update({"internal_id": internal_id, "last_update":datetime.datetime.now(), 'status':status})
    
    def updateFlowRule(self, flow_rule_id, internal_id=None, status='complete'):
        session = get_session()  
        with session.begin():
            session.query(FlowRuleModel).filter_by(id = flow_rule_id).update({"internal_id": internal_id, "last_update":datetime.datetime.now(), 'status':status})
    
    def getGraphConnections(self, graph_id, endpoint_name):
        #graph_id = self._getGraphID(service_graph_id)
        endpoints = self.getEndpoints(graph_id)
        connections = []
        for endpoint in endpoints:
            if endpoint.name == endpoint_name:
                connections = connections + self.checkConnection(endpoint.id)
        return connections
    
    def checkConnection(self, endpoint_id):
        session = get_session() 
        connections = []
        connections = connections+session.query(GraphConnectionModel).filter_by(endpoint_id_2 = endpoint_id).all()
        connections = connections+session.query(GraphConnectionModel).filter_by(endpoint_id_1 = endpoint_id).all()
        return connections

    def getNodeID(self, graph_id):
        session = get_session()
        return session.query(GraphModel.node_id).filter_by(id = graph_id).one().node_id

    def setNodeID(self, graph_id, node_id):
        session = get_session()
        with session.begin():
            logging.debug(session.query(GraphModel).filter_by(id = graph_id).update({"node_id":node_id}))
    
    def updateEndpointType(self, graph_endpoint_id, endpoint_type):
        session = get_session()  
        with session.begin():
            session.query(EndpointModel).filter_by(graph_endpoint_id = graph_endpoint_id).update({"type": endpoint_type})

    def addEndpointResource(self, endpoint_id, endpoint_type, port_id, session_id):
        session = get_session()  
        with session.begin():
            if endpoint_type is not None and "interface" in endpoint_type:

                endpoint_resource_ref = EndpointResourceModel(endpoint_id=endpoint_id,
                                                              resource_type='port',
                                                              resource_id=port_id)
                session.add(endpoint_resource_ref)
                    
    def getEndpoints(self, graph_id):
        session = get_session()  
        return session.query(EndpointModel).filter_by(graph_id = graph_id).all()
    
    
    def get_instantiated_nffg(self, user_id):
        session_id = self.user_session.get_active_user_session(user_id)
        nffg = self.get_nffg(session_id.id)    
        return nffg

    def deletePort(self, port_id, graph_id, vnf_id=None):
        session = get_session()
        with session.begin():
            if vnf_id is None:
                session.query(PortModel).filter_by(graph_id = graph_id).filter_by(id = port_id).delete()
            else:
                session.query(PortModel).filter_by(graph_id = graph_id).filter_by(vnf_id = vnf_id).delete()

    def deleteFlowspecFromPort(self, port_id):
        session = get_session()
        with session.begin():
            flow_rules_ref = session.query(FlowRuleModel.id).\
                filter(FlowRuleModel.id == ActionModel.flow_rule_id).\
                filter(FlowRuleModel.id == MatchModel.flow_rule_id).\
                filter(MatchModel.port_in == port_id).\
                filter(MatchModel.port_in_type == 'port').all()
            for flow_rule_ref in flow_rules_ref:
                session.query(FlowRuleModel).filter_by(id = flow_rule_ref.id).delete()
                session.query(MatchModel).filter_by(flow_rule_id = flow_rule_ref.id).delete()
                session.query(ActionModel).filter_by(flow_rule_id = flow_rule_ref.id).delete()
    
    
            
    def deleteActions(self, flow_rule_id):
        session = get_session()
        with session.begin():
            session.query(ActionModel).filter_by(flow_rule_id = flow_rule_id).delete()
    
    
            
    
            
    
    
    
    def getPortFromInternalID(self, internal_id, graph_id):
        session = get_session()  
        try:
            return session.query(PortModel).filter_by(internal_id=internal_id).filter_by(graph_id=graph_id).one()
        except Exception as ex:
            logging.error(ex)
            raise PortNotFound("Port Not Found for internal ID: "+str(internal_id))
        
    def _getPort(self, port_db_id):
        session = get_session()  
        try:
            return session.query(PortModel).filter_by(id=port_db_id).one()
        except Exception as ex:
            logging.error(ex)
            raise PortNotFound("Port Not Found for db id: "+str(port_db_id))
    
    def _getGraph(self, graph_id):
        session = get_session()  
        try:
            return session.query(GraphModel).filter_by(id=graph_id).one()
        except Exception as ex:
            logging.error(ex)
            raise GraphNotFound("Graph not found for db id: "+str(graph_id))
    
    def _getGraphID(self, service_graph_id):
        session = get_session()  
        try:
            session_id = Session().get_active_user_session_by_nf_fg_id(service_graph_id).id
            return session.query(GraphModel).filter_by(session_id=session_id).one().id
        except Exception as ex:
            logging.error(ex)
            raise GraphNotFound("Graph not found for service graph id: "+str(service_graph_id))
    
    def _getEndpoint(self, endpoint_id):
        session = get_session()  
        try:
            return session.query(EndpointModel).filter_by(id=endpoint_id).one()
        except Exception as ex:
            logging.error(ex)
            raise EndpointNotFound("Endpoint not found - id: "+str(endpoint_id))
    
    def _getEndpointID(self, graph_endpoint_id, graph_id):
        session = get_session()  
        try:
            return session.query(EndpointModel).filter_by(graph_endpoint_id=graph_endpoint_id).filter_by(graph_id=graph_id).one().id
        except Exception as ex:
            logging.error(ex)
            raise EndpointNotFound("Endpoint not found - graph_endpoint_id: "+str(graph_endpoint_id)+" - graph_id: "+str(graph_id))