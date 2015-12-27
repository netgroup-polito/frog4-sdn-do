'''
Created on Oct 23, 2015

@author: fabiomignini
'''
from odl_ca_core.sql.sql_server import get_session
from odl_ca_core.sql.graph_session import ActionModel, EndpointModel, EndpointResourceModel, FlowRuleModel, GraphSessionModel, MatchModel, PortModel, VlanModel 

session = get_session()
session.query(ActionModel).delete()
session.query(EndpointModel).delete()
session.query(EndpointResourceModel).delete()
session.query(FlowRuleModel).delete()
session.query(GraphSessionModel).delete()
session.query(MatchModel).delete()
session.query(PortModel).delete()
session.query(VlanModel).delete()

print("Database sessions deleted")
