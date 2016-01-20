'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta

Singleton Class.
A the end of this file the 'initialize' method is called
in order to create the unique instance.
'''

import configparser, os, inspect, logging
from odl_do.exception import WrongConfigurationFile 


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
            config.read(self.__abs_path+'/config/default-config.ini')
            
            # [basic_config]
            self.__BASIC_CONFIG_IP = config.get('basic_config','ip')
            self.__BASIC_CONFIG_PORT = config.get('basic_config','port')
            self.__BASIC_CONFIG_TIMEOUT = config.get('basic_config','timeout')
            
            # [vlan]
            self.__VLAN_AVAILABLE_IDS = config.get('vlan','available_ids')
            self.__set_available_vlan_ids_array()
            
            # [authentication]
            self.__AUTH_TOKEN_EXPIRATION = config.get('authentication','token_expiration')
            
            # [log]
            self.__LOG_FILE = self.__abs_path+"/"+config.get('log', 'file')
            self.__LOG_VERBOSE = config.getboolean('log', 'verbose')
            self.__LOG_DEBUG = config.getboolean('log', 'debug')
            
            # [database]
            self.__DATABASE_CONNECTION = config.get('database','connection')
            db_file = os.path.basename(self.__DATABASE_CONNECTION)
            self.__DATABASE_CONNECTION = self.__DATABASE_CONNECTION.replace(db_file,self.__abs_path+"/"+db_file)
            
            # [opendaylight]
            self.__ODL_USERNAME = config.get('opendaylight','odl_username')
            self.__ODL_PASSWORD = config.get('opendaylight','odl_password')
            self.__ODL_ENDPOINT = config.get('opendaylight','odl_endpoint')
            self.__ODL_VERSION = config.get('opendaylight','odl_version')
            
            # [messaging]
            self.__DD_NAME = config.get('messaging','dd_name')
            self.__DD_BROKER_ADDRESS = config.get('messaging','dd_broker_address')
            self.__DD_TENANT_NAME = config.get('messaging','dd_tenant_name')
            self.__DD_TENANT_KEY = self.__abs_path+"/"+config.get('messaging','dd_tenant_key')
            
            # [resource_description_topic]
            self.__MSG_RESDESC_TOPIC = config.get('resource_description_topic','msg_resdesc_topic')
            self.__MSG_RESDESC_FILE = self.__abs_path+"/"+config.get('resource_description_topic','msg_resdesc_file')

            # Start logging
            self.log_configuration()
        except Exception as ex:
            raise WrongConfigurationFile(str(ex))
        
        
        
    def log_configuration(self):
        log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s'
        if self.LOG_DEBUG is True:
            log_level = logging.DEBUG
            requests_log = logging.getLogger("requests")
            requests_log.setLevel(logging.WARNING)
            sqlalchemy_log = logging.getLogger('sqlalchemy.engine')
            sqlalchemy_log.setLevel(logging.WARNING)
        elif self.LOG_VERBOSE is True:
            log_level = logging.INFO
            requests_log = logging.getLogger("requests")
            requests_log.setLevel(logging.WARNING)
        else:
            log_level = logging.WARNING
        logging.basicConfig( filename=self.LOG_FILE, level=log_level, 
                             format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
    
    
    def __set_available_vlan_ids_array(self):
        pass
    
    
    
    @property
    def BASIC_CONFIG_IP(self):
        return self.__BASIC_CONFIG_IP
    
    @property
    def BASIC_CONFIG_PORT(self):
        return self.__BASIC_CONFIG_PORT
    
    @property
    def BASIC_CONFIG_TIMEOUT(self):
        return self.__BASIC_CONFIG_TIMEOUT
    
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

conf = Configuration()
conf.initialize()