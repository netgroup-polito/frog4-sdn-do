'''
Created on Jun 22, 2015

@author: fabiomignini
'''
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from odl_ca_core.config import Configuration

sqlserver = Configuration()._DATABASE_CONNECTION

def create_session():
    
    '''
    TODO: create the sqlite db if not exists
    
        1) check if sqlserver starts with 'sqlite://';
        2) check if the db file exists (set a db_exist_flag);
        3) sqlalchemy.create_engine create the db file automatically if it does not exist;
        4) if db_exist_flag is True call a sql file to create all tables.
    '''
    
    engine = sqlalchemy.create_engine(sqlserver) # connect to server
    session = sessionmaker()
    session.configure(bind=engine,autocommit=True)
    return session()

def get_session():
    return create_session()