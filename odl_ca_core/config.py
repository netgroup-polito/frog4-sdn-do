'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''
import ConfigParser, os, inspect
from odl_ca_core.exception import WrongConfigurationFile 


class Configuration(object):
    
    _instance = None
    _AUTH_SERVER = None
    
    def __new__(cls, *args, **kwargs):
        
        if not cls._instance:
            cls._instance = super(Configuration, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance 
    
    def __init__(self):
        self.inizialize()
    
    def inizialize(self): 
        config = ConfigParser.RawConfigParser()
        base_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0])).rpartition('/')[0]
        try:
            if base_folder == "":
                config.read(base_folder+'configuration/orchestrator.conf')
            else:
                config.read(base_folder+'/configuration/orchestrator.conf')
            
            # [basic_config]
            self._BASIC_CONFIG_IP = config.get('basic_config','ip')
            self._BASIC_CONFIG_PORT = config.get('basic_config','port')
            self._BASIC_CONFIG_TIMEOUT = config.get('basic_config','timeout')
            
            # [log]
            self._LOG_FILE = config.get('log', 'file')
            self._LOG_VERBOSE = config.getboolean('log', 'verbose')
            self._LOG_DEBUG = config.getboolean('log', 'debug')
            
            # [database]
            self._DATABASE_CONNECTION = config.get('database','connection')
            
            # [opendaylight]
            self._ODL_USERNAME = config.get('opendaylight','odl_username')
            self._ODL_PASSWORD = config.get('opendaylight','odl_password')
            self._ODL_ENDPOINT = config.get('opendaylight','odl_endpoint')
            self._ODL_VERSION = config.get('opendaylight','odl_version')

                
        except Exception as ex:
            raise WrongConfigurationFile(str(ex))
    
    
    
    @property
    def BASIC_CONFIG_IP(self):
        return self._BASIC_CONFIG_IP
    
    @property
    def BASIC_CONFIG_PORT(self):
        return self._BASIC_CONFIG_PORT
    
    @property
    def BASIC_CONFIG_TIMEOUT(self):
        return self._BASIC_CONFIG_TIMEOUT
    
    @property
    def LOG_FILE(self):
        return self._LOG_FILE
    
    @property
    def LOG_VERBOSE(self):
        return self._LOG_VERBOSE
    
    @property
    def LOG_DEBUG(self):
        return self._LOG_DEBUG
    
    @property
    def DATABASE_CONNECTION(self):
        return self._DATABASE_CONNECTION
    
    @property
    def ODL_USERNAME(self):
        return self._ODL_USERNAME
    
    @property
    def ODL_PASSWORD(self):
        return self._ODL_PASSWORD
    
    @property
    def ODL_ENDPOINT(self):
        return self._ODL_ENDPOINT
    
    @property
    def ODL_VERSION(self):
        return self._ODL_VERSION
    
    
    
