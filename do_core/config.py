'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta

'''

import configparser, os, inspect, logging, json
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

        self.__abs_path = \
            os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0])).rpartition(
                '/')[0]
        '''
        The absolute path of the main directory (it ends without '/')
        will be added to every 'path-like' configuration string.
        Using absolute paths avoids a lot of kinds of problems.
        '''

        try:
            # TODO add config file as parameter
            config.read(self.__abs_path + '/config/config.ini')

            # [domain_orchestrator]
            self.__ORCHESTRATOR_PORT = config.get('domain_orchestrator', 'port')
            self.__ORCHESTRATOR_IP = config.get('domain_orchestrator', 'ip')

            # [log]
            self.__LOG_FILE = self.__abs_path + "/" + config.get('log', 'file')
            self.__LOG_VERBOSE = config.getboolean('log', 'verbose')
            self.__LOG_DEBUG = config.getboolean('log', 'debug')
            self.log_configuration()

            # [vlan]
            self.__VLAN_AVAILABLE_IDS = config.get('vlan', 'available_ids')
            self.__ALLOWED_VLANS = self.__set_available_vlan_ids_array(self.__VLAN_AVAILABLE_IDS)

            # [physical_ports]
            ports_json = config.get('physical_ports', 'ports')
            self.__PORTS = json.loads(ports_json)

            # [authentication]
            self.__AUTH_TOKEN_EXPIRATION = config.get('authentication', 'token_expiration')

            # [database]
            self.__DATABASE_CONNECTION = config.get('database', 'connection')
            db_file = os.path.basename(self.__DATABASE_CONNECTION)
            self.__DATABASE_CONNECTION = self.__DATABASE_CONNECTION.replace(db_file, self.__abs_path + "/" + db_file)
            self.__DATABASE_DUMP_FILE = self.__abs_path + "/" + config.get('database', 'database_name')

            # [network_controller]
            self.__CONTROLLER_NAME = config.get('network_controller', 'controller_name')

            # [opendaylight]
            self.__ODL_USERNAME = config.get('opendaylight', 'odl_username')
            self.__ODL_PASSWORD = config.get('opendaylight', 'odl_password')
            self.__ODL_ENDPOINT = config.get('opendaylight', 'odl_endpoint')
            self.__ODL_VERSION = config.get('opendaylight', 'odl_version')

            # [onos]
            self.__ONOS_USERNAME = config.get('onos', 'onos_username')
            self.__ONOS_PASSWORD = config.get('onos', 'onos_password')
            self.__ONOS_ENDPOINT = config.get('onos', 'onos_endpoint')
            self.__ONOS_VERSION = config.get('onos', 'onos_version')

            # [ovsdb]
            self.__OVSDB_NODE_IP = config.get('ovsdb', 'ovsdb_node_ip')
            self.__OVSDB_NODE_PORT = config.get('ovsdb', 'ovsdb_node_port')
            self.__OVSDB_IP = config.get('ovsdb', 'ovsdb_ip')

            # [messaging]
            self.__DD_ACTIVATE = config.getboolean('messaging', 'dd_activate')
            self.__DD_NAME = config.get('messaging', 'dd_name')
            self.__DD_BROKER_ADDRESS = config.get('messaging', 'dd_broker_address')
            self.__DD_TENANT_NAME = config.get('messaging', 'dd_tenant_name')
            # self.__DD_TENANT_KEY = self.__abs_path + "/" + config.get('messaging', 'dd_tenant_key')
            self.__DD_TENANT_KEY = config.get('messaging', 'dd_tenant_key')

            # [domain_description]
            self.__DOMAIN_DESCRIPTION_TOPIC = config.get('domain_description', 'domain_description_topic')
            self.__DOMAIN_DESCRIPTION_FILE = self.__abs_path + "/" + config.get('domain_description',
                                                                                'domain_description_file')
            self.__CAPABILITIES_APP_NAME = config.get('domain_description', 'capabilities_app_name')

            # [other_options]
            self.__OO_CONSOLE_PRINT = config.get('other_options', 'console_print')

            print(self.__PORTS)

        except Exception as ex:
            raise WrongConfigurationFile(str(ex))

    def log_configuration(self):
        log_format = '%(asctime)s %(levelname)s %(message)s - %(filename)s:%(lineno)s'
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
        logging.basicConfig(filename=self.LOG_FILE, level=log_level, format=log_format,
                            datefmt='%m/%d/%Y %I:%M:%S %p:%r')
        logging.info("[CONFIG] Logging just starded!")

    def __set_available_vlan_ids_array(self, vid_ranges):

        '''
        Expected vid_ranges = "280-289,62,737,90-95,290-299,13-56,92,57-82,2-5,12"
        '''

        def __getKey(item):
            return item[0]

        vid_array = []
        if isinstance(vid_ranges, str):
            ranges = vid_ranges.split(",")
        else:
            ranges = vid_ranges

        for r in ranges:
            r = str(r)
            exs = r.split("-")
            if len(exs) == 1:
                exs.append(exs[0])
            elif len(exs) != 2:
                continue

            min_vlan_id = int(exs[0])
            max_vlan_id = int(exs[1])
            if (min_vlan_id > max_vlan_id):
                continue

            vid_array.append([min_vlan_id, max_vlan_id])
            logging.debug("[CONFIG] - Available VLAN ID - Range: '" + r + "'")

        if len(vid_array) == 0:
            logging.error("[CONFIG] - VLAN ID - No available vlan id read from '" + vid_ranges + "'")
            return []
        else:
            return sorted(vid_array, key=__getKey)

    @property
    def ORCHESTRATOR_PORT(self):
        return self.__ORCHESTRATOR_PORT

    @property
    def ORCHESTRATOR_IP(self):
        return self.__ORCHESTRATOR_IP

    @property
    def VLAN_AVAILABLE_IDS(self):
        return self.__VLAN_AVAILABLE_IDS

    @property
    def ALLOWED_VLANS(self):
        return self.__ALLOWED_VLANS

    @property
    def PORTS(self):
        return self.__PORTS

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
    def OVSDB_NODE_IP(self):
        return self.__OVSDB_NODE_IP

    @property
    def OVSDB_NODE_PORT(self):
        return self.__OVSDB_NODE_PORT

    @property
    def OVSDB_IP(self):
        return self.__OVSDB_IP

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
    def DOMAIN_DESCRIPTION_TOPIC(self):
        return self.__DOMAIN_DESCRIPTION_TOPIC

    @property
    def DOMAIN_DESCRIPTION_FILE(self):
        return self.__DOMAIN_DESCRIPTION_FILE

    @property
    def CAPABILITIES_APP_NAME(self):
        return self.__CAPABILITIES_APP_NAME

    @property
    def OO_CONSOLE_PRINT(self):
        return self.__OO_CONSOLE_PRINT


conf = Configuration()
conf.initialize()
