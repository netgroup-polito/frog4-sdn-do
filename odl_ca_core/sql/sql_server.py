'''
Created on Jun 22, 2015

@author: fabiomignini
'''
import sqlalchemy, os
from sqlalchemy.orm import sessionmaker
from odl_ca_core.config import Configuration


def get_session():
    '''
    The only one function to create a connection with the database.
    Make some checks before the effective session creation.
    Raise the FileNotFoundError exception (if SQLite is used).
    '''
    sqlserver = Configuration().DATABASE_CONNECTION
    
    # Manage SQLite connection
    if sqlserver[:6] == "sqlite":
        if __check_sqlite_database(sqlserver):
            return __create_session(sqlserver)
        else:
            raise FileNotFoundError("SQLite Database File not found")
    
    # Return standard session
    return __create_session()

def try_session():
    '''
    Create and close a database connection.
    Raise some exceptions and print some informations.
    '''
    print("Testing database connection...")
    s = get_session()
    s.close_all()
    print("Database connection estabilished correctly.\n")
 
def __create_session(sqlserver):
    engine = sqlalchemy.create_engine(sqlserver) # connect to server
    session = sessionmaker()
    session.configure(bind=engine,autocommit=True)
    return session()

def __check_sqlite_database(sqlserverconnection):
    # sqlserverconnection starts with "sqlite:///"
    #filename = os.path.basename(sqlserverconnection)
    filename = sqlserverconnection[10:]
    return os.path.exists(filename)

    
    