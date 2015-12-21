'''
Created on Jun 22, 2015

@author: fabiomignini
'''
import sqlalchemy, sqlite3, os.path, os
from sqlalchemy.orm import sessionmaker
from odl_ca_core.config import Configuration

sqlserver = Configuration().DATABASE_CONNECTION

def create_session():
    
    '''
    TODO: create the sqlite db if not exists
    
        1) check if sqlserver starts with 'sqlite://';
            import os.path
            os.path.basename(your_path)
            
        2) check if the db file exists (set a db_exist_flag);
            import os.path
            db_exist_flag = os.path.exists("/db.sqlite") #return True or False
            
        3) sqlalchemy.create_engine create the db file automatically if it does not exist;
        
        4) if db_exist_flag is True call a sql file to create all tables;
            conn = sqlite3.connect(sqlserver)
            c = conn.cursor()
            c.execute(...)
            
    '''    
    engine = sqlalchemy.create_engine(sqlserver) # connect to server
    session = sessionmaker()
    session.configure(bind=engine,autocommit=True)
    return session()

def get_session():
    return create_session()


def session_create_database():

    # Relative file addresses
    db_filename = "../db.sqlite"
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
    
    