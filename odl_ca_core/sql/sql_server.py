'''
Created on Jun 22, 2015

@author: fabiomignini
'''
import sqlalchemy, sqlite3, os.path, os
from sqlalchemy.orm import sessionmaker
from odl_ca_core.config import Configuration

sqlserver = Configuration().DATABASE_CONNECTION

def create_session():
    #TODO: check if db exists
    engine = sqlalchemy.create_engine(sqlserver) # connect to server
    session = sessionmaker()
    session.configure(bind=engine,autocommit=True)
    return session()

def get_session():
    return create_session()


def session_create_database():

    # Relative file addresses
    db_filename = "../db.sqlite3"
    dbdumpfile = "../db_dump.sqlite.sql"

    if os.path.exists(db_filename):
        return
    print("ddd")
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
    
    