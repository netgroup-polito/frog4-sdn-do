'''
Created on Oct 1, 2014

@author: fabiomignini
'''
from sqlalchemy import Column, DateTime, func, VARCHAR, Text, not_, desc
from odl_ca_core.sql.sql_server import get_session
from sqlalchemy.ext.declarative import declarative_base
from odl_ca_core.exception import sessionNotFound


import datetime
import logging

Base = declarative_base()


# TODO: 'ingress_node','egress_node' ...eliminare funzioni


class SessionModel(Base):
    '''
    Maps the database table session
    '''
    __tablename__ = 'graph'
    attributes = ['session_id', 'user_id', 'graph_id', 'graph_name', 'status','started_at',
                  'last_update','error','ended']
    session_id = Column(VARCHAR(64), primary_key=True)
    user_id = Column(VARCHAR(64))
    graph_id = Column(Text)
    graph_name = Column(Text)
    status = Column(Text)
    started_at = Column(Text)
    last_update = Column(DateTime, default=func.now())
    error = Column(Text)
    ended = Column(DateTime)
    


class Session(object):
    def __init__(self):
        pass
    
    def inizializeSession(self, session_id, user_id, graph_id, graph_name):
        '''
        inizialize the session in db
        '''
        session = get_session()  
        with session.begin():
            session_ref = SessionModel(session_id=session_id, user_id = user_id, graph_id = graph_id, 
                                started_at = datetime.datetime.now(), graph_name=graph_name,
                                last_update = datetime.datetime.now(), status='inizialization')
            session.add(session_ref)
        pass

    def updateStatus(self, session_id, status):
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(session_id = session_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now(), 'status':status})

    def updateUserID(self, session_id, user_id):
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(session_id = session_id).filter_by(ended = None).filter_by(error = None).update({"user_id":user_id})
    
    def updateSessionNode(self, session_id, ingress_node, egress_node):
        '''
        store the session in db
        '''
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(session_id = session_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now(), "ingress_node":ingress_node, "egress_node": egress_node})
    
    def updateSession(self, session_id, ingress_node, egress_node, status):
        '''
        store the session in db
        '''
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(session_id = session_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now(), "ingress_node":ingress_node, "egress_node": egress_node, 'status':status})
                
    '''   
    def update_session(self, graph_id, profile, infrastructure):
        session = get_session()  
        with session.begin():
            session.query(SessionModel).filter_by(graph_id = graph_id).filter_by(ended = None).filter_by(error = None).update({"last_update":datetime.datetime.now()})
    '''
            
    def get_active_user_session(self, user_id):
        '''
        returns if exists an active session of the user
        '''
        session = get_session()
        session_ref = session.query(SessionModel).filter_by(user_id = user_id).filter_by(ended = None).filter_by(error = None).first()
        if session_ref is None:
            raise sessionNotFound("Session Not Found")
        return session_ref
    
    
    def set_ended(self, session_id):
        '''
        Set the ended status for the session identified with session_id
        '''
        session = get_session() 
        with session.begin():       
            session.query(SessionModel).filter_by(session_id=session_id).update({"ended":datetime.datetime.now()}, synchronize_session = False)
    
    def set_error_by_nffg_id(self, nffg_id):
        '''
        Set the error status for the active session associated to the nffg id passed
        '''
        session = get_session()
        with session.begin():     
            logging.debug("Put session for nffg "+str(nffg_id)+" in error")
            session.query(SessionModel).filter_by(graph_id=nffg_id).filter_by(ended = None).filter_by(error = None).update({"error":datetime.datetime.now()}, synchronize_session = False)
        
    def set_error(self, session_id):
        '''
        Set the error status for the active session associated to the user id passed
        '''
        session = get_session()
        with session.begin():
            logging.debug("Put session for session "+str(session_id)+" in error")
            session.query(SessionModel).filter_by(session_id=session_id).filter_by(ended = None).filter_by(error = None).update({"error":datetime.datetime.now()}, synchronize_session = False)
    
    def checkSession(self, user_id, token, graph_id = None):
        '''
        return true if there is already an active session of the user
        '''
        session = get_session()
        if graph_id is None:
            user_session = session.query(SessionModel).filter_by(user_id = user_id).filter_by(ended = None).filter_by(error = None).first()
        else:
            # TODO:
            raise NotImplemented()
        
        if user_session is None:
            return False
        else:
            return True
    
    def get_active_user_session_from_id(self, session_id):
        session = get_session()
        with session.begin():  
            user_session = session.query(SessionModel).filter_by(session_id=session_id).filter_by(ended = None).filter_by(error = None).first()
            if not user_session:
                raise sessionNotFound("Session Not Found") 
        return user_session
    
    def get_active_user_session_by_nf_fg_id(self, user_id, graph_id, error_aware=True):
        session = get_session()
        if error_aware:
            session_ref = session.query(SessionModel).filter_by(user_id = user_id).filter_by(graph_id = graph_id).filter_by(ended = None).filter_by(error = None).first()
        else:
            session_ref = session.query(SessionModel).filter_by(user_id = user_id).filter_by(graph_id = graph_id).filter_by(ended = None).order_by(desc(SessionModel.started_at)).first()
        if session_ref is None:
            raise sessionNotFound("Session Not Found, for servce graph id: "+str(graph_id))        
        return session_ref
    
    def get_profile_id_from_active_user_session(self, user_id):
        session = get_session()
        session_ref = session.query(SessionModel.graph_id).filter_by(user_id = user_id).filter_by(ended = None).filter_by(error = None).first()
        
        if session_ref is None:
            raise sessionNotFound("Session Not Found")
        return session_ref.graph_id
    
    def get_graph_info(self,session_id):
        session = get_session()
        return session.query(SessionModel.graph_id, SessionModel.graph_name).filter_by(session_id = session_id).one()
        
        
    def checkEgressNode(self, node, profile):
        """
        Return False if the only ingress point in the node
        is that that we are deleting
        """
        session = get_session()
        egs = session.query(SessionModel).filter_by(egress_node = node).filter(not_(Session.profile.contains(profile))).all()
        if egs is not None and len(egs) == 0:
            return False
        return True 

    def checkIngressNode(self, node, profile):
        """
        Return False if the only ingress point in the node
        is that that we are deleting
        """
        session = get_session()
        ings = session.query(SessionModel).filter_by(ingress_node = node).filter(not_(Session.profile.contains(profile))).all()
        if ings is not None and len(ings) == 0:
            return False
        return True