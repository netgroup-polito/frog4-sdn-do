'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''
import ConfigParser, os, inspect, logging
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
            config.read(base_folder+'/configuration.conf')
            
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
    
    
    
