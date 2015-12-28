'''
Created on Jun 22, 2015

@author: fabiomignini
'''
import sqlalchemy, sqlite3, os
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






# Work in progress
def __session_create_database():

    # Relative file addresses
    db_filename = "../db.sqlite3"
    dbdumpfile = "../db_dump.sqlite.sql"

    if os.path.exists(db_filename):
        return
    if os.path.exists(dbdumpfile) == False:
        return
    
    # Set write permissions on the database file
    new_db_filename = open(db_filename,'w')
    os.chmod(db_filename, 0o666)
    new_db_filename.close()
    
    # Read the dump file
    in_file = open(dbdumpfile,"r")
    sqldump = in_file.read()
    if len(sqldump)<1:
        return    
    
    '''
    sqlite3.complete_statement(sql) returns True if the string sql contains 
    one or more complete SQL statements terminated by semicolons. 
    It does not verify that the SQL is syntactically correct, only that there are 
    no unclosed string literals and the statement is terminated by a semicolon.
    This can be used to build a shell for SQLite.
    '''
    if sqlite3.complete_statement(sqldump):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.executescript(sqldump)
        conn.close()
        
    return
    
    