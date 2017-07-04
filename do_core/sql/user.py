'''
Created on 18 set 2015

@author: Andrea
'''

from sqlalchemy import Column, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
import logging, random, time

from sqlalchemy.sql.functions import func

from do_core.sql.sql_server import get_session
from do_core.exception import UserNotFound, TenantNotFound

Base = declarative_base()

class UserModel(Base):
    '''
    Maps the database table user
    '''
    __tablename__ = 'user'
    attributes = ['id', 'name', 'pwdhash', 'tenant_id', 'mail', 'token', 'token_timestamp']
    id = Column(VARCHAR(64), primary_key=True)
    username = Column(VARCHAR(64))
    pwdhash = Column(VARCHAR(64))
    tenant_id = Column(VARCHAR(64))
    mail = Column(VARCHAR(64))
    token = Column(VARCHAR(64))
    token_timestamp = Column(VARCHAR(64))


class TenantModel(Base):
    '''
    Maps the database table tenant
    '''
    __tablename__ = 'tenant'
    attributes = ['id', 'name', 'description']
    id = Column(VARCHAR(64), primary_key=True)
    name = Column(VARCHAR(64))
    description = Column(VARCHAR(128))
    

class User(object):
    
    def __init__(self):
        pass

    def addUser(self, username, pwdhash, tenant_id, mail):
        session = get_session()
        max_id = session.query(func.max(UserModel.id).label("max_id")).one().max_id
        if max_id is None:
            user_id = 0
        else:
            user_id = int(max_id)+1
        with session.begin():
            user_ref = UserModel(id=user_id, username=username, pwdhash=pwdhash, tenant_id=tenant_id, mail=mail)
            session.add(user_ref)

    def getUserByUsername(self, username):
        session = get_session()
        try:
            return session.query(UserModel).filter_by(username = username).one()
        except Exception as ex:
            logging.error(ex)
            raise UserNotFound("User not found: "+str(username)+" (username)")
    
    def getUserByToken(self, token):
        session = get_session()
        try:
            return session.query(UserModel).filter_by(token = token).one()
        except Exception as ex:
            logging.error(ex)
            raise UserNotFound("Token not found: "+str(token))
        
    def getUserByID(self, user_id):
        session = get_session()
        try:
            return session.query(UserModel).filter_by(id = user_id).one()
        except Exception as ex:
            logging.error(ex)
            raise UserNotFound("User not found: "+str(user_id)+" (id)")
    
    def getTenantName(self, tenant_id):
        session = get_session()
        try:
            return session.query(TenantModel).filter_by(id = tenant_id).one().name
        except Exception as ex:
            logging.error(ex)
            raise TenantNotFound("Tenant not found: "+str(tenant_id))
    
    def setPwdHash(self, user_id, pwdhash):
        session = get_session()
        with session.begin():
            session.query(UserModel).filter_by(id=user_id).update({"pwdhash":pwdhash})
    
    def getNewToken(self, user_id):
        exists = True
        while exists:
            token = hex(random.getrandbits(256))[2:] #len=64
            timestamp = time.time()
            exists = self.checkToken(token)
        
        timestamp = int(timestamp)
        return token,timestamp

    def setNewToken(self, user_id, token, timestamp):
        session = get_session()
        with session.begin():
            session.query(UserModel).filter_by(id=user_id).update({"token":token,"token_timestamp":timestamp})
    
    def checkToken(self, token):
        session = get_session()
        try:
            session.query(UserModel).filter_by(token = token).one()
            return True
        except Exception:
            return False

        
        



