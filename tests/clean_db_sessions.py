'''
Created on Oct 23, 2015

@author: fabiomignini
'''
from odl_ca_core.sql.sql_server import get_session
from odl_ca_core.sql.graph2 import ActionModel, EndpointModel, EndpointResourceModel, FlowRuleModel, SessionModel, MatchModel, PortModel, GraphConnectionModel 

session = get_session()
session.query(ActionModel).delete()
session.query(EndpointModel).delete()
session.query(EndpointResourceModel).delete()
session.query(FlowRuleModel).delete()
session.query(SessionModel).delete()
session.query(GraphConnectionModel).delete()
session.query(MatchModel).delete()
session.query(PortModel).delete()
#session.query(SessionModel).delete()

print "Database sessions deleted"
