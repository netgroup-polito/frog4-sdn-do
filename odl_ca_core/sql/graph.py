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

    def get_nffg(self, graph_id):
        nffg = NF_FG()
        session = get_session()
        graph_ref = session.query(GraphModel).filter_by(id = graph_id).one()
        service_graph_info_ref = Session().get_service_graph_info(graph_ref.session_id)

        if graph_ref.partial is True:
            nffg.id = graph_ref.id
        else:
            nffg.id = service_graph_info_ref.service_graph_id
        nffg.name = service_graph_info_ref.service_graph_name
        nffg.db_id = graph_ref.id
        
        flow_rules_ref = session.query(FlowRuleModel).filter_by(graph_id = graph_id).all()
        for flow_rule_ref in flow_rules_ref:
            if flow_rule_ref.type == 'external':
                continue
            flow_rule = FlowRule(_id=flow_rule_ref.graph_flow_rule_id, priority=int(flow_rule_ref.priority),
                      db_id=flow_rule_ref.id, internal_id=flow_rule_ref.internal_id)
            nffg.addFlowRule(flow_rule)
            try:
                match_ref = session.query(MatchModel).filter_by(flow_rule_id = flow_rule.db_id).one()
                
                if match_ref.port_in_type == 'endpoint':
                    end_point_ref = session.query(EndpointModel).filter_by(id = match_ref.port_in).first()
                    port_in = match_ref.port_in_type+':'+end_point_ref.graph_endpoint_id
                    
                match = Match(port_in=port_in, ether_type=match_ref.ether_type, vlan_id=match_ref.vlan_id,
                       vlan_priority=match_ref.vlan_priority, source_mac=match_ref.source_mac,
                        dest_mac=match_ref.dest_mac, source_ip=match_ref.source_ip, dest_ip=match_ref.dest_ip,
                        tos_bits=match_ref.tos_bits, source_port=match_ref.source_port, dest_port=match_ref.dest_port,
                         protocol=match_ref.protocol, db_id=match_ref.id)
                flow_rule.match = match
            except NoResultFound:
                logging.info("Found flowrule without a match")
            try:
                actions_ref = session.query(ActionModel).filter_by(flow_rule_id = flow_rule.db_id).all()
                for action_ref in actions_ref:
                    output = None
                    if action_ref.output_type == 'endpoint':
                        end_point_ref = session.query(EndpointModel).filter_by(id = action_ref.output).first()
                        output = action_ref.output_type+':'+end_point_ref.graph_endpoint_id
                    
                    action = Action(output=output, controller=action_ref.controller, drop=action_ref._drop, set_vlan_id=action_ref.set_vlan_id,
                                    set_vlan_priority=action_ref.set_vlan_priority, pop_vlan=action_ref.pop_vlan, 
                                    set_ethernet_src_address=action_ref.set_ethernet_src_address, 
                                    set_ethernet_dst_address=action_ref.set_ethernet_dst_address, 
                                    set_ip_src_address=action_ref.set_ip_src_address, set_ip_dst_address=action_ref.set_ip_dst_address, 
                                    set_ip_tos=action_ref.set_ip_tos, set_l4_src_port=action_ref.set_l4_src_port, 
                                    set_l4_dst_port=action_ref.set_l4_dst_port, output_to_queue=action_ref.output_to_queue,
                                    db_id=action_ref.id)
                    flow_rule.actions.append(action)
            except NoResultFound:
                logging.debug("Found flowrule without actions")
            
                            
        end_points_ref = session.query(EndpointModel).filter_by(graph_id = graph_id).all()
        for end_point_ref in end_points_ref:
            end_point = EndPoint(_id=end_point_ref.graph_endpoint_id, name=end_point_ref.name, _type=end_point_ref.type,
                                 db_id=end_point_ref.id, internal_id=end_point_ref.internal_id)
            nffg.addEndPoint(end_point)
            
            
            # End_point resource
            end_point_resorces_ref = session.query(EndpointResourceModel).filter_by(endpoint_id = end_point_ref.id).all()
            for end_point_resorce_ref in end_point_resorces_ref:
                if end_point_resorce_ref.resource_type == 'port':
                    try:
                        port = self._getPort(end_point_resorce_ref.resource_id)
                    except PortNotFound:
                        raise Exception("I dont'know when I'm here. There was a continue here, why?")
                        #continue
                        
                    end_point.node = port.location
                    end_point.switch_id = port.virtual_switch
                    end_point.interface = port.graph_port_id
                    end_point.vlan_id = port.vlan_id
                    
            graph_connections_ref = session.query(GraphConnectionModel).filter_by(endpoint_id_1 = end_point_ref.id).all()
            for graph_connection_ref in graph_connections_ref:
                ext_endpoint = self._getEndpoint(graph_connection_ref.endpoint_id_2)
                ext_nffg_id = ext_endpoint.graph_id
                ext_end_point_id = ext_endpoint.graph_endpoint_id       
                end_point.remote_endpoint_id = ext_nffg_id+':'+ext_end_point_id
        return nffg
        
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
    
    def updateNFFG(self, nffg, graph_id, partial=False):
        session = get_session()  
        with session.begin():
            self.id_generator(nffg=nffg, session_id=None, update=True, graph_id=graph_id)
            #graph_ref = GraphModel(id=nffg.db_id, session_id=session_id, partial=partial)
            #session.add(graph_ref)           
                            
            for flow_rule in nffg.flow_rules:
                if flow_rule.status == 'new' or flow_rule.status is None:
                    self.addFlowRule(nffg.db_id, flow_rule, nffg)            

            for endpoint in nffg.end_points:
                if endpoint.status == 'new' or endpoint.status is None:        
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
    
    def delete_session(self, session_id):
        session = get_session()
        graphs_ref = session.query(GraphModel).filter_by(session_id = session_id).all()
        for graph_ref in graphs_ref:
            self.delete_graph(graph_ref.id)
    
    def delete_graph(self, graph_id):
        session = get_session()
        with session.begin():
            session.query(GraphModel).filter_by(id = graph_id).delete()
            
            session.query(PortModel).filter_by(graph_id = graph_id).delete()
              
            flow_rules_ref = session.query(FlowRuleModel).filter_by(graph_id = graph_id).all()
            for flow_rule_ref in flow_rules_ref:
                session.query(MatchModel).filter_by(flow_rule_id = flow_rule_ref.id).delete()
                session.query(ActionModel).filter_by(flow_rule_id = flow_rule_ref.id).delete()
            session.query(FlowRuleModel).filter_by(graph_id = graph_id).delete()
            endpoints_ref = session.query(EndpointModel.id).filter_by(graph_id = graph_id).all()
            for endpoint_ref in endpoints_ref:
                session.query(GraphConnectionModel).filter_by(endpoint_id_1 = endpoint_ref.id).delete()
                session.query(GraphConnectionModel).filter_by(endpoint_id_2 = endpoint_ref.id).delete()
                session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_ref.id).delete()
            session.query(EndpointModel).filter_by(graph_id = graph_id).delete()
        
    def id_generator(self, nffg, session_id, update=False, graph_id=None):
        graph_base_id = self._get_higher_graph_id()
        port_base_id = self._get_higher_port_id()
        endpoint_base_id = self._get_higher_endpoint_id()
        flow_rule_base_id = self._get_higher_flow_rule_id()
        action_base_id = self._get_higher_action_id()
        if graph_base_id is not None:
            self.graph_id = int(graph_base_id) + 1
        else:
            self.graph_id = 0
        
        # TODO: remove
        self.vnf_id = 0
        
        if port_base_id is not None:
            self.port_id = int(port_base_id) + 1
        else:
            self.port_id = 0
        if endpoint_base_id is not None:
            self.endpoint_id = int(endpoint_base_id) + 1
        else:
            self.endpoint_id = 0
        if flow_rule_base_id is not None:
            self.flow_rule_id = int(flow_rule_base_id) + 1
        else:
            self.flow_rule_id = 0
        if action_base_id is not None:
            self.action_id = int(action_base_id) + 1
        else:
            self.action_id = 0  
        if update == False:
            nffg.db_id = self.graph_id
        else:
            session = get_session()  
            if graph_id is None:
                graphs_ref = session.query(GraphModel).filter_by(session_id = session_id).all()
                nffg.db_id = graphs_ref[0].id
            else:
                nffg.db_id = graph_id
        for flow_rule in nffg.flow_rules: 
            if flow_rule.status is None or flow_rule.status == "new": 
                flow_rule.db_id = self.flow_rule_id
                self.flow_rule_id = self.flow_rule_id +1
            for action in flow_rule.actions:
                if flow_rule.status is None or flow_rule.status == "new":
                    action.db_id = self.action_id
                    self.action_id = self.action_id + 1
        for endpoint in nffg.end_points:
            if endpoint.status is None or endpoint.status == "new":   
                endpoint.db_id = self.endpoint_id 
                self.endpoint_id = self.endpoint_id + 1
    
    def _get_higher_graph_id(self):  
        session = get_session()  
        return session.query(func.max(GraphModel.id).label("max_id")).one().max_id
        
    def _get_higher_port_id(self):
        session = get_session()  
        return session.query(func.max(PortModel.id).label("max_id")).one().max_id
        
    def _get_higher_endpoint_id(self):
        session = get_session()  
        return session.query(func.max(EndpointModel.id).label("max_id")).one().max_id
        
    def _get_higher_flow_rule_id(self):
        session = get_session()  
        return session.query(func.max(FlowRuleModel.id).label("max_id")).one().max_id
    
    def _get_higher_action_id(self):
        session = get_session()  
        return session.query(func.max(ActionModel.id).label("max_id")).one().max_id
    
    def getGraphs(self, session_id):
        session = get_session()
        return session.query(GraphModel).filter_by(session_id=session_id).all()
    
    def getFlowRules(self, graph_id):
        session = get_session()
        return session.query(FlowRuleModel).filter_by(graph_id = graph_id).all()
    
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
    
    def setEndpointLocation(self, graph_id, graph_endpoint_id, location):
        session = get_session()
        with session.begin():
            assert (session.query(EndpointModel).filter_by(graph_id = graph_id).filter_by(graph_endpoint_id = graph_endpoint_id).update({"location": location}) == 1)

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
    
    def deleteFlowRule(self, flow_rule_id):
        session = get_session()
        with session.begin():
            session.query(FlowRuleModel).filter_by(id = flow_rule_id).delete()
            session.query(MatchModel).filter_by(flow_rule_id = flow_rule_id).delete()
            session.query(ActionModel).filter_by(flow_rule_id = flow_rule_id).delete()
            
    def deleteActions(self, flow_rule_id):
        session = get_session()
        with session.begin():
            session.query(ActionModel).filter_by(flow_rule_id = flow_rule_id).delete()
    
    def deleteEndpoint(self, graph_endpoint_id, graph_id):
        session = get_session()
        with session.begin():
            session.query(EndpointModel).filter_by(graph_id = graph_id).filter_by(graph_endpoint_id = graph_endpoint_id).delete()
    
    def deleteEndpointResource(self, endpoint_id):
        session = get_session()
        with session.begin():
            session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_id).delete()
            
    def deleteEndpointResourceAndResources(self, endpoint_id):
        session = get_session()
        with session.begin():
            end_point_resources_ref = session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_id).all()
            for end_point_resource_ref in end_point_resources_ref:
                if end_point_resource_ref.resource_type == 'port':
                    session.query(PortModel).filter_by(id = end_point_resource_ref.resource_id).delete()
                elif end_point_resource_ref.resource_type == 'flowrule':
                    session.query(FlowRuleModel).filter_by(id = end_point_resource_ref.resource_id).delete()
                    session.query(MatchModel).filter_by(flow_rule_id = end_point_resource_ref.resource_id).delete()
                    session.query(ActionModel).filter_by(flow_rule_id = end_point_resource_ref.resource_id).delete()    
            session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_id).delete()
            
    def getEndpointResource(self, endpoint_id, resource_type=None):
        session = get_session()
        resources=[]
        with session.begin():
            if resource_type is None:
                end_point_resources_ref = session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_id).all()
            else:
                end_point_resources_ref = session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_id).filter_by(resource_type = resource_type).all()
            for end_point_resource_ref in end_point_resources_ref:
                if end_point_resource_ref.resource_type == 'port':
                    port_ref = session.query(PortModel).filter_by(id = end_point_resource_ref.resource_id).one()
                    port = Port(_id=port_ref.graph_port_id, name=port_ref.name, _type=port_ref.type,
                      db_id=port_ref.id, internal_id=port_ref.internal_id)
                    resources.append(port)
                elif end_point_resource_ref.resource_type == 'flowrule':
                    flow_rule_ref = session.query(FlowRuleModel).filter_by(id = end_point_resource_ref.resource_id).one()
                    flow_rule = FlowRule(_id=flow_rule_ref.graph_flow_rule_id, priority=int(flow_rule_ref.priority),
                      db_id=flow_rule_ref.id, internal_id=flow_rule_ref.internal_id, node_id=flow_rule_ref.node_id, _type=flow_rule_ref.type, status=flow_rule_ref.status)
                    resources.append(flow_rule)
                #TODO: actions and match not considered
            return resources
                        
    def deleteGraphConnection(self, endpoint_id1):
        #only unilateral 
        session = get_session()
        with session.begin():
            session.query(GraphConnectionModel).filter_by(endpoint_id_1 = endpoint_id1).delete()
    
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