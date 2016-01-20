from doubledecker.clientSafe import ClientSafe
from odl_do.config import Configuration
from threading import Thread
import logging


class DD_Publish(ClientSafe):
    
    def __init__(self, name, dealerurl, customer, keyfile, topic, message):
        super().__init__(name, dealerurl, customer, keyfile)
        self.__dc_topic = topic
        self.__dc_message = message
    
    def on_reg(self):
        self.publish(self.__dc_topic, self.__dc_message)
        #self.shutdown()
        return

    def on_data(self, dest, msg):
        pass
    def on_pub(self, src, topic, msg):
        pass    
    def on_discon(self):
        pass
    def unsubscribe(self, topic, scope):
        pass
    def on_cli(self, dummy, other_dummy):
        pass
    


class Messaging(object): # Singleton Class
    
    _instance = None

    __debug_exit = False # inhibit this class
    
    __publish_domain_config = None
    __thread_publish_domain_config = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Messaging, cls).__new__(cls, *args, **kwargs)
        return cls._instance 
    
    def __init__(self):
        return
        
    
    def PublishDomainConfig(self):
        if self.__debug_exit:
            return
        
        try:
            in_file = open(Configuration().MSG_RESDESC_FILE,"r")
            msg_resdesc_file = in_file.read()
        
            if self.__publish_domain_config is None:
                dd_publish = DD_Publish(Configuration().DD_NAME,
                                        Configuration().DD_BROKER_ADDRESS,
                                        Configuration().DD_TENANT_NAME,
                                        Configuration().DD_TENANT_KEY,
                                        Configuration().MSG_RESDESC_TOPIC, 
                                        msg_resdesc_file)
                thread = Thread(target=dd_publish.start)
                thread.start()
                self.__publish_domain_config = dd_publish
                self.__thread_publish_domain_config = thread
            else:    
                self.__publish_domain_config.publish(Configuration().MSG_RESDESC_TOPIC, msg_resdesc_file)
            
        except Exception as ex:
            logging.error(ex)




