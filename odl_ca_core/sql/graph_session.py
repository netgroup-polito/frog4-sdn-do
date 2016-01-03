'''
Created on Jun 20, 2015

@author: fabiomignini
@author: giacomoratta
'''

import datetime, logging, uuid

from nffg_library.nffg import NF_FG, EndPoint, FlowRule, Match, Action

from sqlalchemy import Column, VARCHAR, Boolean, Integer, DateTime, Text, asc, desc, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound

from odl_ca_core.config import Configuration
from odl_ca_core.sql.sql_server import get_session
from odl_ca_core.exception import PortNotFound



Base = declarative_base()
sqlserver = Configuration().DATABASE_CONNECTION


class GraphSessionModel(Base):
    __tablename__ = 'graph_session'
    attributes = ['session_id', 'user_id', 'graph_id', 'graph_name', 'status',
                  'started_at', 'last_update', 'error', 'ended', 'description']
    session_id = Column(VARCHAR(64), primary_key=True)
    user_id = Column(VARCHAR(64))
    graph_id = Column(Text)     # id in the json [see "forwarding-graph" section]
    graph_name = Column(Text)   # name in the json [see "forwarding-graph" section]
    status = Column(Text)       # = ( initialization | complete | updating | deleted | error )
    started_at = Column(DateTime)
    last_update = Column(DateTime, default=func.now())
    error = Column(DateTime)
    ended = Column(DateTime)
    description = Column(VARCHAR(256))


class PortModel(Base):
    __tablename__ = 'port'
    attributes = ['id', 'graph_port_id', 'status', 'switch_id', 'session_id'
                  'mac_address', 'ipv4_address', 'vlan_id','gre_key', 'creation_date','last_update' ]
    id = Column(Integer, primary_key=True)
    graph_port_id = Column(VARCHAR(64)) # endpoint interface in the json [see "interface" section]
    status = Column(VARCHAR(64))        # = ( initialization | complete | error )
    switch_id = Column(VARCHAR(64))
    session_id = Column(VARCHAR(64))
    
    # port characteristics
    mac_address = Column(VARCHAR(64))
    ipv4_address = Column(VARCHAR(64))
    vlan_id = Column(VARCHAR(64))
    gre_key = Column(VARCHAR(64))
    creation_date = Column(DateTime)
    last_update = Column(DateTime, default=func.now())
    
    
    
class EndpointModel(Base):
    __tablename__ = 'endpoint'
    attributes = ['id', 'graph_endpoint_id','name','type','session_id']
    id = Column(Integer, primary_key=True) 
    graph_endpoint_id = Column(VARCHAR(64)) # id in the json [see "end-points" section]
    name = Column(VARCHAR(64))  # name in the json [see "end-points" section]
    type = Column(VARCHAR(64))  # = ( internal | interface | interface-out | vlan | gre ) [see "end-points" section]
    session_id = Column(VARCHAR(64))
    
    
    
class EndpointResourceModel(Base):
    '''
        resource_type: flow-rule type must have the resource_id equal to the flow-rules
                       that connect the end-point to an external end-point.
    '''
    __tablename__ = 'endpoint_resource'
    attributes = ['endpoint_id', 'resource_type', 'resource_id']
    endpoint_id = Column(Integer, primary_key=True)
    resource_type = Column(VARCHAR(64), primary_key=True) # = ( port | flow-rule )
    resource_id = Column(Integer, primary_key=True)
    
    

class FlowRuleModel(Base):
    __tablename__ = 'flow_rule'
    attributes = ['id', 'graph_flow_rule_id', 'internal_id', 'session_id', 
                  'switch_id', 'type', 'priority','status', 'creation_date','last_update','description']
    id = Column(Integer, primary_key=True)
    graph_flow_rule_id = Column(VARCHAR(64)) # id in the json [see "flow-rules" section]
    internal_id = Column(VARCHAR(64)) # auto-generated id, for the same graph_flow_rule_id
    session_id = Column(VARCHAR(64))
    
    switch_id = Column(VARCHAR(64))
    type = Column(VARCHAR(64))      # = ( NULL | external )
    priority = Column(VARCHAR(64))  # priority in the json [see "flow-rules" section] 
    status = Column(VARCHAR(64))    # = ( initialization | complete | error )
    creation_date = Column(DateTime)
    last_update = Column(DateTime, default=func.now())
    description = Column(VARCHAR(128))
    
    
    
class MatchModel(Base):
    __tablename__ = 'match'
    attributes = ['id', 'flow_rule_id', 'port_in_type', 'port_in', 'ether_type','vlan_id','vlan_priority', 'source_mac','dest_mac','source_ip',
                 'dest_ip','tos_bits','source_port', 'dest_port', 'protocol']
    id = Column(Integer, primary_key=True)
    flow_rule_id = Column(Integer)      # = FlowRuleModel.id
    port_in_type = Column(VARCHAR(64))  # = ( port | endpoint )
    
    # match characteristics
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
    __tablename__ = 'action'
    attributes = ['id', 'flow_rule_id', 'output_type', 'output', 'controller', '_drop', 'set_vlan_id','set_vlan_priority','pop_vlan', 'set_ethernet_src_address',
                  'set_ethernet_dst_address','set_ip_src_address','set_ip_dst_address', 'set_ip_tos','set_l4_src_port','set_l4_dst_port', 'output_to_queue']    
    id = Column(Integer, primary_key=True)
    flow_rule_id = Column(Integer)      # = FlowRuleModel.id
    output_type = Column(VARCHAR(64))   # = ( port | endpoint )
    
    # action characteristics
    output = Column(VARCHAR(64))        # es. output port, endpoint interface
    controller = Column(Boolean)        # if 'true' it sends packets to controller (es. CONTROLLER:65535) 
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



class VlanModel(Base):
    __tablename__ = 'vlan'
    attributes = ['id', 'flow_rule_id', 'switch_id', 'port_in', 'vlan_in', 'port_out', 'vlan_out']
    id = Column(Integer, primary_key=True)
    flow_rule_id = Column(Integer)
    switch_id = Column(VARCHAR(64))
    port_in = Column(Integer)
    vlan_in = Column(VARCHAR(64))
    port_out = Column(Integer)
    vlan_out = Column(VARCHAR(64))






class GraphSession(object):
    def __init__(self):
        pass
    
    
    def addNFFG(self, nffg, user_id):
            
        # New session id
        session_id = self.__get_univocal_session_id()
        
        # Add a new record in GraphSession
        self.dbStoreGraphSessionFromNffgObject(session_id, user_id, nffg)

            
        # [ ENDPOINTS ]
        for endpoint in nffg.end_points:
            
            # Add a new endpoint
            endpoint_id = self.dbStoreEndpoint(session_id, None, endpoint.id, endpoint.name, endpoint.type)
            endpoint.db_id = endpoint_id
            
            # Add end-point resources
            # End-point attached to something that is not another graph
            if endpoint.type=="interface" or endpoint.type=="vlan":
                self.addPort(session_id, endpoint_id, None, endpoint.interface, endpoint.switch_id, endpoint.vlan_id, 'complete')

        # [ FLOW RULES ]
        for flow_rule in nffg.flow_rules:
            self.addFlowrule(session_id, None, flow_rule, nffg)
            
        return session_id
    
    
    
    def updateNFFG(self, nffg, session_id):     
                            
        # [ ENDPOINTS ]
        for endpoint in nffg.end_points:
            
            # Add a new endpoint
            if endpoint.status == 'new' or endpoint.status is None:
                endpoint_id = self.dbStoreEndpoint(session_id, None, endpoint.id, endpoint.name, endpoint.type)
                endpoint.db_id = endpoint_id

                # Add end-point resources
                # End-point attached to something that is not another graph
                if endpoint.type=="interface" or endpoint.type=="vlan":
                    self.addPort(session_id, endpoint_id, None, endpoint.interface, endpoint.switch_id, endpoint.vlan_id, 'complete')
        
        # [ FLOW RULES ]
        for flow_rule in nffg.flow_rules:
            if flow_rule.status == 'new' or flow_rule.status is None:
                self.addFlowrule(session_id, None, flow_rule, nffg)            





    
    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DATABASE INTERFACE - GET section "def get*"
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''

    def getEndpointByGraphID(self, graph_endpoint_id, session_id):
        session = get_session()
        try:
            ep = session.query(EndpointModel).filter_by(session_id = session_id).filter_by(graph_endpoint_id = graph_endpoint_id).one()
            return ep
        except:
            return None
    
    
    def getEndpointsBySessionID(self, session_id):
        session = get_session()
        try:
            ep = session.query(EndpointModel).filter_by(session_id = session_id).all()
            return ep
        except:
            return None
    
    
    def getEndpointResources(self, endpoint_id):
        session = get_session()
        try:
            eprs = session.query(EndpointResourceModel).filter_by(endpoint_id = endpoint_id).all()
            return eprs
        except:
            return None
    
    
    def getFlowruleByID(self, flow_rule_id=None):
        try:
            session = get_session()
            return session.query(FlowRuleModel).filter_by(id=flow_rule_id).one()
        except:
            return None
        return None
        
    
    def getFlowrules(self, session_id, graph_flow_rule_id=None):
        session = get_session()
        if graph_flow_rule_id is None:
            return session.query(FlowRuleModel).filter_by(session_id = session_id).all()
        else:
            return session.query(FlowRuleModel).filter_by(session_id = session_id).filter_by(graph_flow_rule_id = graph_flow_rule_id).all()


    def getUserGraphSession(self, user_id, graph_id, error_aware=True):
        session = get_session()
        if error_aware:
            session_ref = session.query(GraphSessionModel).filter_by(user_id = user_id).filter_by(graph_id = graph_id).filter_by(ended = None).filter_by(error = None).first()
        else:
            session_ref = session.query(GraphSessionModel).filter_by(user_id = user_id).filter_by(graph_id = graph_id).filter_by(ended = None).order_by(desc(GraphSessionModel.started_at)).first()
        #if session_ref is None:
        #    raise sessionNotFound("Session Not Found, for servce graph id: "+str(graph_id))        
        return session_ref
    
    
    
    
    
    
    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DATABASE INTERFACE - INSERT section "def add*"
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
    
    def addFlowrule(self, session_id, switch_id, flow_rule, nffg=None):   
                  
        # FlowRule
        flow_rule_db_id = self.dbStoreFlowrule(session_id, flow_rule, None, switch_id)
        
        # Match
        if nffg is not None and flow_rule.match is not None:
            match_db_id = flow_rule_db_id
            port_in_type = None
            port_in = None
            if flow_rule.match.port_in.split(':')[0] == 'endpoint':
                port_in_type = 'endpoint'
                port_in = nffg.getEndPoint(flow_rule.match.port_in.split(':')[1]).db_id
                self.dbStoreEndpointResourceFlowrule(port_in, flow_rule_db_id)
            self.dbStoreMatch(flow_rule.match, flow_rule_db_id, match_db_id, port_in=port_in, port_in_type=port_in_type)
        
        # Actions
        if nffg is not None and len(flow_rule.actions)>0:
            for action in flow_rule.actions:
                output_type = None
                output_port = None
                if action.output != None and action.output.split(':')[0] == 'endpoint':
                    output_type = 'endpoint'
                    output_port = nffg.getEndPoint(action.output.split(':')[1]).db_id
                    self.dbStoreEndpointResourceFlowrule(output_port, flow_rule_db_id)
                self.dbStoreAction(action, flow_rule_db_id, None, output=output_port, output_type=output_type)

        return flow_rule_db_id
    
    
    def addPort(self, session_id, endpoint_id, port_id, graph_port_id, switch_id, vlan_id, status):
        port_id = self.dbStorePort(session_id, port_id, graph_port_id, switch_id, vlan_id, status)
        self.dbStoreEndpointResourcePort(endpoint_id, port_id)






    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DATABASE INTERFACE - UPDATE section "def update*"
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
    
    def updateEnded(self, session_id):
        session = get_session() 
        with session.begin():       
            session.query(GraphSessionModel).filter_by(session_id=session_id).update({"ended":datetime.datetime.now()}, synchronize_session = False)


    def updateError(self, session_id):
        session = get_session()
        with session.begin():
            session.query(GraphSessionModel).filter_by(session_id=session_id).update({"error":datetime.datetime.now(),"status":"deleted"}, synchronize_session = False)


    def updateStatus(self, session_id, status, error=False):
        session = get_session()
        with session.begin():
            session.query(GraphSessionModel).filter_by(session_id=session_id).update({"last_update":datetime.datetime.now(), 'status':status})






    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DATABASE INTERFACE - DELETE section "def delete*"
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
    
    def deleteEndpoint(self, endpoint_id):
        # delete from tables: EndpointModel.
        session = get_session()
        with session.begin():
            session.query(EndpointModel).filter_by(id = endpoint_id).delete()


    def deleteEndpointByGraphID(self, graph_endpoint_id, session_id):
        # delete from tables: EndpointModel.
        session = get_session()
        with session.begin():
            session.query(EndpointModel).filter_by(session_id = session_id).filter_by(graph_endpoint_id = graph_endpoint_id).delete()
    

    def deleteFlowrule(self,  flow_rule_id):
        # delete from tables: FlowRuleModel, MatchModel, ActionModel, VlanModel, EndpointResourceModel.
        session = get_session()
        with session.begin():
            session.query(FlowRuleModel).filter_by(id=flow_rule_id).delete()
            session.query(MatchModel).filter_by(flow_rule_id=flow_rule_id).delete()
            session.query(ActionModel).filter_by(flow_rule_id=flow_rule_id).delete()
            session.query(VlanModel).filter_by(flow_rule_id=flow_rule_id).delete()
            session.query(EndpointResourceModel).filter_by(resource_id=flow_rule_id).filter_by(resource_type='flow-rule').delete()
    
    
    def deletePort(self,  port_id):
        # delete from tables: PortModel, EndpointResourceModel.
        session = get_session()
        with session.begin():
            session.query(PortModel).filter_by(id = port_id).delete()
            session.query(EndpointResourceModel).filter_by(resource_id=port_id).filter_by(resource_type='port').delete()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # TODO: clean and improve!
    def getNFFG(self, session_id):
        nffg = NF_FG()
        session = get_session()
        session_ref = session.query(GraphSessionModel).filter_by(session_id=session_id).one()

        nffg.id = session_ref.graph_id
        nffg.name = session_ref.graph_name
        
        flow_rules_ref = session.query(FlowRuleModel).filter_by(session_id = session_id).all()
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
            
                            
        end_points_ref = session.query(EndpointModel).filter_by(session_id = session_id).all()
        for end_point_ref in end_points_ref:
            end_point = EndPoint(_id=end_point_ref.graph_endpoint_id, name=end_point_ref.name, _type=end_point_ref.type,
                                 db_id=end_point_ref.id)
            nffg.addEndPoint(end_point)
            
            # End_point resource
            end_point_resorces_ref = session.query(EndpointResourceModel).filter_by(endpoint_id = end_point_ref.id).all()
            for end_point_resorce_ref in end_point_resorces_ref:
                if end_point_resorce_ref.resource_type == 'port':
                    try:
                        port = self._getPort(end_point_resorce_ref.resource_id)
                    except PortNotFound:
                        raise Exception("I dont'know when I'm here. There was a continue here, why?")
                        # TODO: manage this exception
                        #continue
                        
                    #end_point.node = port.location
                    end_point.switch_id = port.switch_id
                    end_point.interface = port.graph_port_id
                    end_point.vlan_id = port.vlan_id
            # TODO: remove or integrate GraphConnectionModel, remote endpoint, etc.
        return nffg
    
    
    
    
  
  
    '''
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
        DB STORE FUNCTIONS "def dbStore*"
        These functions works only with the database to add new records.
    * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * 
    '''
    
    def dbStoreAction(self, action, flow_rule_db_id, action_db_id=None, output=None, output_type=None):    
        session = get_session()
        
        if action_db_id is None:
            action_db_id = session.query(func.max(ActionModel.id).label("max_id")).one().max_id
            if action_db_id is None:
                action_db_id = 0
            else:
                action_db_id = int(action_db_id) + 1
        
        if output is None:
            output=action.output
            
        with session.begin():
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
            return action_ref


    def dbStoreEndpoint(self, session_id, endpoint_id, graph_endpoint_id, name, _type):
        session = get_session()
        if endpoint_id is None:
            endpoint_id = session.query(func.max(EndpointModel.id).label("max_id")).one().max_id
            if endpoint_id is None:
                endpoint_id = 0
            else:
                endpoint_id=int(endpoint_id)+1
        with session.begin():
            endpoint_ref = EndpointModel(id=endpoint_id, graph_endpoint_id=graph_endpoint_id, 
                                         session_id=session_id, name=name, type=_type)
            session.add(endpoint_ref)
            return endpoint_id
    
    
    def dbStoreEndpointResourcePort(self, endpoint_id, port_id):
        session = get_session()
        with session.begin():
            ep_res_ref = EndpointResourceModel(endpoint_id=endpoint_id, resource_type='port', resource_id=port_id)
            session.add(ep_res_ref)

                
    def dbStoreEndpointResourceFlowrule(self, endpoint_id, flow_rule_id):
        session = get_session()
        with session.begin():
            ep_res_ref = EndpointResourceModel(endpoint_id=endpoint_id,resource_type='flow-rule',resource_id=flow_rule_id)
            session.add(ep_res_ref)
    

    def dbStoreFlowrule(self, session_id, flow_rule, flow_rule_db_id, switch_id):
        session = get_session()
        if flow_rule_db_id is None:
            flow_rule_db_id = session.query(func.max(FlowRuleModel.id).label("max_id")).one().max_id
            if flow_rule_db_id is None:
                flow_rule_db_id = 0
            else:
                flow_rule_db_id=int(flow_rule_db_id)+1
        with session.begin():
            flow_rule_ref = FlowRuleModel(id=flow_rule_db_id, internal_id=flow_rule.internal_id, 
                                       graph_flow_rule_id=flow_rule.id, session_id=session_id, switch_id=switch_id,
                                       priority=flow_rule.priority,  status=flow_rule.status, description=flow_rule.description,
                                       creation_date=datetime.datetime.now(), last_update=datetime.datetime.now(), type=flow_rule.type)
            session.add(flow_rule_ref)
            return flow_rule_db_id
    
    
    def dbStoreGraphSessionFromNffgObject(self, session_id, user_id, nffg):
        session = get_session()
        with session.begin():
            graphsession_ref = GraphSessionModel(session_id=session_id, user_id=user_id, graph_id=nffg.id, 
                                started_at = datetime.datetime.now(), graph_name=nffg.name,
                                last_update = datetime.datetime.now(), status='inizialization', description=nffg.description)
            session.add(graphsession_ref)
    
    
    def dbStoreMatch(self, match, flow_rule_db_id, match_db_id, port_in=None, port_in_type=None):
        session = get_session()
        with session.begin():
            
            if port_in is None:
                port_in=match.port_in
            
            # Flowrule and match have a 1:1 relationship,
            # so the match record can have the same id of the flowrule record!
            match_ref = MatchModel(id=match_db_id, flow_rule_id=flow_rule_db_id, 
                                   port_in_type=port_in_type, port_in=port_in,
                                   ether_type=match.ether_type, vlan_id=match.vlan_id,
                                   vlan_priority=match.vlan_priority, source_mac=match.source_mac,
                                   dest_mac=match.dest_mac, source_ip=match.source_ip,
                                   dest_ip=match.dest_ip, tos_bits=match.tos_bits,
                                   source_port=match.source_port, dest_port=match.dest_port,
                                   protocol=match.protocol)
            session.add(match_ref)
            return match_ref
    
    
    def dbStorePort(self, session_id, port_id, graph_port_id, switch_id, vlan_id, status):
        session = get_session()
        if port_id is None:
            port_id = session.query(func.max(PortModel.id).label("max_id")).one().max_id
            if port_id is None:
                port_id = 0
            else:
                port_id=int(port_id)+1
        with session.begin():
            port_ref = PortModel(id=port_id, 
                                 graph_port_id=graph_port_id,
                                 session_id=session_id, status=status, 
                                 switch_id=switch_id,
                                 vlan_id=vlan_id,
                                 creation_date=datetime.datetime.now(), 
                                 last_update=datetime.datetime.now())
            session.add(port_ref)
            return port_id

        
    
    
    
    
    
    
    
    
    
    
    
    


        
    
    
    
    










    
    
    
    
    # used by getNFFG only
    def _getPort(self, port_id):
        session = get_session()  
        try:
            return session.query(PortModel).filter_by(id=port_id).one()
        except Exception as ex:
            logging.error(ex)
            raise PortNotFound("Port "+str(port_id)+" not found.")


    
    def __get_univocal_session_id(self):
        '''
        Compute a new session id 32 byte long.
        Check if it is already exists: if yes, repeat the computation. 
        '''
        session = get_session()
        rows = session.query(GraphSessionModel.session_id).all()
        
        while True:
            session_id = uuid.uuid4().hex
            found = False
            for row in rows:
                if(row.session_id == session_id):
                    found = True
                    break
            if found==False:
                return session_id
    
    
    
    
    
    
    
    '''
    Work in progress...
    '''
            
    def vlanTracking_add(self, flow_rule_id, switch_id, vlan_in, port_in, vlan_out, port_out):
        session = get_session()
        
        max_id = session.query(func.max(VlanModel.id).label("max_id")).one().max_id
        if max_id  is None:
            max_id = 0
        else:
            max_id = int(max_id)+1
        
        with session.begin():    
            vlan_ref = VlanModel(id=max_id, flow_rule_id=flow_rule_id, switch_id=switch_id, vlan_in=vlan_in, port_in=port_in, vlan_out=vlan_out, port_out=port_out)
            session.add(vlan_ref) 



    def vlanTracking_check(self, port_in, port_out, vlan_in=None, vlan_out=None, next_switch_id=None, next_port_in=None):
        # return vlan_out (None or in [1,4094])
        session = get_session()
        
        # TODO: Search for vlan out collisions on current switch
        #query_ref = session.query(VlanModel.id).filter_by().all()
        
        # TODO: Search for vlan in collisions on next switch
        if next_switch_id is not None:
            query_ref = session.query(VlanModel.id).filter_by(vlan_in=vlan_out).filter_by(switch_id=next_switch_id).filter_by(port_in=next_port_in).all()
            if len(query_ref)>0:
                return None
        
        # Vlan out is compliant with actual and next switches
        return vlan_out
    
    
    
    def vlanInIsBusy(self, switch_id, vlan_in, port_in):
        session = get_session()
        query_ref = session.query(VlanModel.id).filter_by(vlan_in=vlan_in).filter_by(switch_id=switch_id).filter_by(port_in=port_in).all()
        if len(query_ref)>0:
            return True
        return False


    def vlanTracking_new_vlan_out(self, port_in, port_out, vlan_in=None, vlan_out=None, next_switch_id=None, next_port_in=None):
        # return vlan_out (None or in [1,4094])
        session = get_session()
        new_vlan_in = 0
        
        # TODO: Search an egress vlan id suitable for the current switch
        
        # Search an ingress vlan id suitable for the next switch
        # TODO: improve the search algorithm
        if next_switch_id is not None:
            try:
                query_ref = session.query(VlanModel).filter_by(switch_id=next_switch_id).filter_by(port_in=next_port_in).order_by(asc(VlanModel.vlan_in)).all()
                new_vlan_in=2
                if len(query_ref)>0:
                    prev_vlan_in = 1
                    for q in query_ref:
                        
                        if(q.vlan_in is None):
                            continue
                        
                        this_vlan_in = int(q.vlan_in)
                        
                        if prev_vlan_in==this_vlan_in or this_vlan_in<=1:
                            continue
                        
                        if (this_vlan_in-prev_vlan_in)<=1 :
                            prev_vlan_in = this_vlan_in
                            continue
                        
                        new_vlan_in = prev_vlan_in+1
                        if new_vlan_in<=0 and prev_vlan_in>=4095:
                            new_vlan_in=-1
                        break                   
            except:
                new_vlan_in=0
        return new_vlan_in
        
    
    