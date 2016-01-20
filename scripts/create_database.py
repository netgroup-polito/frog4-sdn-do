import sqlite3, os
from odl_do.config import Configuration

def session_create_database():

    db_filename = Configuration().DATABASE_CONNECTION
    
    # Remove first 10 characters "sqlite:///"
    db_filename = db_filename[10:]
    
    # Dump file
    db_dumpfile = "config/db.dump.sql"

    if os.path.exists(db_dumpfile) == False:
        print("'"+db_dumpfile+"' not exists!")
        return
    
    print("Set write permissions on the database file")
    new_db_filename = open(db_filename,'w')
    os.chmod(db_filename, 0o666)
    new_db_filename.close()
    
    print("Read the dump file")
    in_file = open(db_dumpfile,"r")
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
    print("Creating all tables and loading data on the database...")
    if sqlite3.complete_statement(sqldump):
        conn = sqlite3.connect(db_filename)
        cursor = conn.cursor()
        cursor.executescript(sqldump)
        conn.close()
        
    print("Database created successfully.\n\n")
    return



session_create_database()