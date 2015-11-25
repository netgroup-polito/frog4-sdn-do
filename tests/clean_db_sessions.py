'''
Created on Oct 23, 2015

@author: fabiomignini
'''
from odl_ca_core.sql.sql_server import get_session
from odl_ca_core.sql.graph import ActionModel, EndpointModel, EndpointResourceModel, FlowRuleModel, GraphModel, MatchModel, PortModel, GraphConnectionModel 
from odl_ca_core.sql.session import SessionModel

session = get_session()
session.query(ActionModel).delete()
session.query(EndpointModel).delete()
session.query(EndpointResourceModel).delete()
session.query(FlowRuleModel).delete()
session.query(GraphModel).delete()
session.query(GraphConnectionModel).delete()
session.query(MatchModel).delete()
session.query(PortModel).delete()
session.query(SessionModel).delete()

print "Database sessions deleted"
