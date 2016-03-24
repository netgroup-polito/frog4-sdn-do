'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta

'''

import configparser, os, inspect, logging
from do_core.exception import WrongConfigurationFile 


class Configuration(object):
    
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Configuration, cls).__new__(cls, *args, **kwargs)
        return cls._instance 
    
    def __init__(self):
        return      
        
    
    def initialize(self): 
        config = configparser.RawConfigParser()
        
        self.__abs_path = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])).rpartition('/')[0]
        '''
        The absolute path of the main directory (it ends without '/')
        will be added to every 'path-like' configuration string.
        Using absolute paths avoids a lot of kinds of problems.
        '''
        
        try:
            config.read(self.__abs_path+'/config/config.ini')
            
            # [log]
            self.__LOG_FILE = self.__abs_path+"/"+config.get('log', 'file')
            self.__LOG_VERBOSE = config.getboolean('log', 'verbose')
            self.__LOG_DEBUG = config.getboolean('log', 'debug')
            self.log_configuration()
            
            # [vlan]
            self.__VLAN_AVAILABLE_IDS = config.get('vlan','available_ids')
            
            # [authentication]
            self.__AUTH_TOKEN_EXPIRATION = config.get('authentication','token_expiration')

            # [database]
            self.__DATABASE_CONNECTION = config.get('database','connection')
            db_file = os.path.basename(self.__DATABASE_CONNECTION)
            self.__DATABASE_CONNECTION = self.__DATABASE_CONNECTION.replace(db_file,self.__abs_path+"/"+db_file)
            self.__DATABASE_DUMP_FILE = self.__abs_path+"/"+config.get('database','database_name')
            
            # [network_controller]
            self.__CONTROLLER_NAME = config.get('network_controller','controller_name')
            
            # [opendaylight]
            self.__ODL_USERNAME = config.get('opendaylight','odl_username')
            self.__ODL_PASSWORD = config.get('opendaylight','odl_password')
            self.__ODL_ENDPOINT = config.get('opendaylight','odl_endpoint')
            self.__ODL_VERSION = config.get('opendaylight','odl_version')
            
            # [onos]
            self.__ONOS_USERNAME = config.get('onos','onos_username')
            self.__ONOS_PASSWORD = config.get('onos','onos_password')
            self.__ONOS_ENDPOINT = config.get('onos','onos_endpoint')
            self.__ONOS_VERSION = config.get('onos','onos_version')
            
            # [messaging]
            self.__DD_ACTIVATE = config.getboolean('messaging','dd_activate')
            self.__DD_NAME = config.get('messaging','dd_name')
            self.__DD_BROKER_ADDRESS = config.get('messaging','dd_broker_address')
            self.__DD_TENANT_NAME = config.get('messaging','dd_tenant_name')
            self.__DD_TENANT_KEY = self.__abs_path+"/"+config.get('messaging','dd_tenant_key')
            
            # [resource_description_topic]
            self.__MSG_RESDESC_TOPIC = config.get('resource_description_topic','msg_resdesc_topic')
            self.__MSG_RESDESC_FILE = self.__abs_path+"/"+config.get('resource_description_topic','msg_resdesc_file')
            
            # [other_options]
            self.__OO_CONSOLE_PRINT = config.get('other_options','console_print')
            
        except Exception as ex:
            raise WrongConfigurationFile(str(ex))
        
        
        
    def log_configuration(self):
        log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s'
        if self.__LOG_DEBUG is True:
            log_level = logging.DEBUG
            requests_log = logging.getLogger("requests")
            requests_log.setLevel(logging.WARNING)
            sqlalchemy_log = logging.getLogger('sqlalchemy.engine')
            sqlalchemy_log.setLevel(logging.WARNING)
        elif self.__LOG_DEBUG is True:
            log_level = logging.INFO
            requests_log = logging.getLogger("requests")
            requests_log.setLevel(logging.WARNING)
        else:
            log_level = logging.WARNING
        logging.basicConfig( filename=self.LOG_FILE, level=log_level, 
                             format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
        logging.info("[CONFIG] Logging just starded!")
                
    
    
    @property
    def VLAN_AVAILABLE_IDS(self):
        return self.__VLAN_AVAILABLE_IDS
    
    @property
    def AUTH_TOKEN_EXPIRATION(self):
        return self.__AUTH_TOKEN_EXPIRATION
    
    @property
    def LOG_FILE(self):
        return self.__LOG_FILE
    
    @property
    def LOG_VERBOSE(self):
        return self.__LOG_VERBOSE
    
    @property
    def LOG_DEBUG(self):
        return self.__LOG_DEBUG
    
    @property
    def DATABASE_CONNECTION(self):
        return self.__DATABASE_CONNECTION
    
    @property
    def DATABASE_DUMP_FILE(self):
        return self.__DATABASE_DUMP_FILE
    
    @property
    def CONTROLLER_NAME(self):
        return self.__CONTROLLER_NAME
    
    @property
    def ODL_USERNAME(self):
        return self.__ODL_USERNAME
    
    @property
    def ODL_PASSWORD(self):
        return self.__ODL_PASSWORD
    
    @property
    def ODL_ENDPOINT(self):
        return self.__ODL_ENDPOINT
    
    @property
    def ODL_VERSION(self):
        return self.__ODL_VERSION
    
    @property
    def ONOS_USERNAME(self):
        return self.__ONOS_USERNAME
    
    @property
    def ONOS_PASSWORD(self):
        return self.__ONOS_PASSWORD
    
    @property
    def ONOS_ENDPOINT(self):
        return self.__ONOS_ENDPOINT
    
    @property
    def ONOS_VERSION(self):
        return self.__ONOS_VERSION
    
    @property
    def DD_ACTIVATE(self):
        return self.__DD_ACTIVATE
    
    @property
    def DD_NAME(self):
        return self.__DD_NAME
    
    @property
    def DD_BROKER_ADDRESS(self):
        return self.__DD_BROKER_ADDRESS
    
    @property
    def DD_TENANT_NAME(self):
        return self.__DD_TENANT_NAME
    
    @property
    def DD_TENANT_KEY(self):
        return self.__DD_TENANT_KEY
    
    @property
    def MSG_RESDESC_TOPIC(self):
        return self.__MSG_RESDESC_TOPIC
    
    @property
    def MSG_RESDESC_FILE(self):
        return self.__MSG_RESDESC_FILE
    
    @property
    def OO_CONSOLE_PRINT(self):
        return self.__OO_CONSOLE_PRINT

conf = Configuration()
conf.initialize()