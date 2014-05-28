'''
Created on May 30, 2013

@author: mxu
@target: Provide Database operations
@requires: db_info is a dict, contains host, port, username, password, database keys.
'''

import mysql.connector
import ChorusGlobals
import traceback

def __init_connection(connection):
    host = connection["host"]
    port = connection["port"]
    user = connection["username"]
    passwd = connection["password"]
    database = connection["database"]
    db_handler = mysql.connector.connect(host = host,
                                   port = int(port),
                                   user = user,
                                   passwd = passwd,
                                   database = database)
    ChorusGlobals.get_logger().info("start mysql connection")
    return db_handler

def set_base_db_info(db_config, keep_connection = True):
    global db_info
    try:
        db_info = {
                    "host": db_config['db_addr'],
                    "port": db_config['db_port'],
                    "username": db_config['db_username'],
                    "password": db_config['db_password'],
                    "database": db_config['db_database']
                  }
        if keep_connection:
            db_handler = __init_connection(db_info)
            global default_handler
            default_handler = db_handler
            return db_handler
        else:
            return None
    except Exception, e:
        traceback.print_exc()
        ChorusGlobals.get_logger().critical("Errors %s in db_info format: %s" % (str(e),str(db_info)))
        raise Exception("Errors %s in db_info format: %s" % (str(e),str(db_info)))

def __close_connection(db_handler = None):
    if not db_handler:
        db_handler = default_handler
    cursor = db_handler.cursor()   
    cursor.close()
    db_handler.close()
    ChorusGlobals.get_logger().info("close mysql connection")

def execute_sql(sql, db_handler = None, keep_connection = True):
    '''execute sql and return a list format data'''
    try:
        data = []
        if db_handler:
            conn = db_handler
        else:
            if "default_handler" in globals().keys():
                conn = default_handler
            else:
                keep_connection = False
                conn = __init_connection(db_info)
        cursor = conn.cursor()
        ChorusGlobals.get_logger().info("Execute SQL '%s'" % sql)
        cursor.execute(sql)
        for row in cursor:
            data.append(row) 
        conn.commit()
        
    except Exception, e:
        traceback.print_exc()
        ChorusGlobals.get_logger().critical("Errors in sql execution: %s" % e)
        raise Exception("Errors in sql execution: %s" % e)
                    
    finally:
        if not keep_connection:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            ChorusGlobals.get_logger().info("close mysql connection")
        return data 

def execute_sql_dict(sql, db_handler = None, keep_connection = True):
    '''execute sql and return a dict format data'''
    try:
        data = []
        datadict=[]
        if db_handler:
            conn = db_handler
        else:
            if "default_handler" in globals().keys():
                conn = default_handler
            else:
                keep_connection = False
                conn = __init_connection(db_info)
        cursor = conn.cursor()
        ChorusGlobals.get_logger().info("Execute SQL '%s'" % sql)
        cursor.execute(sql)
        for row in cursor:
            data.append(row)
        for row in data:
            rid=data.index(row)
            celldict={}
            for i in range(len(row)):
                celldict[cursor.column_names[i]]=row[i]
            datadict.append(celldict)
        conn.commit()
        
    except Exception, e:
        traceback.print_exc()
        ChorusGlobals.get_logger().critical("Errors in sql execution: %s" % e)
        raise Exception("Errors in sql execution: %s" % e)
                    
    finally:
        if not keep_connection:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            ChorusGlobals.get_logger().info("close mysql connection")
        return datadict 
