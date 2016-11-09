import time
import hashlib
import json
import logging

from doubledecker.clientSafe import ClientSafe
from do_core.config import Configuration
from threading import Thread

from do_core.netmanager import NetManager
from do_core.resource_description import Singleton, ResourceDescription


class DDClient(ClientSafe):

    def __init__(self, name, dealerurl, customer, keyfile, topic, message):
        super().__init__(name, dealerurl, customer, keyfile)
        self._registered = False
        self.topic = topic
        self.message = message

    def on_data(self, dest, msg):
        print(dest, " sent", msg)

    def on_pub(self, src, topic, msg):
        msg_str = "PUB %s from %s: %s" % (str(topic), str(src), str(msg))
        print(msg_str)

    def on_reg(self):
        self._registered = True
        self.publish(self.topic, self.message)

    def on_discon(self):
        pass

    def on_error(self):
        pass

    def unsubscribe(self, topic, scope):
        pass

    @property
    def REGISTERED(self):
        return self._registered


class Messaging(object, metaclass=Singleton):

    def __init__(self):
        self.dd_class = None
        self.working_thread = None
        self.first_start = True

    def _cold_start(self):
        print(Configuration().DD_TENANT_KEY)
        message = self.read_domain_description_file()
        self.dd_class = DDClient(
            name=Configuration().DD_NAME,
            dealerurl=Configuration().DD_BROKER_ADDRESS,
            customer=Configuration().DD_TENANT_KEY,     # bug in dd??
            keyfile=Configuration().DD_TENANT_KEY,
            topic=Configuration().DOMAIN_DESCRIPTION_TOPIC,
            message=message
        )
        self.working_thread = Thread(target=self.dd_class.start)
        self.working_thread.start()
        logging.info("DoubleDecker client started!")
        logging.info("Publishing domain information: " + message)

    def publish_domain_description(self):
        if self.first_start is True:
            self._cold_start()
            self.first_start = False
            return
        message = self.read_domain_description_file()
        try:
            self.dd_class.publish(Configuration().DOMAIN_DESCRIPTION_TOPIC, message)
            logging.info("Publishing domain information: " + message)
        except ConnectionError:
            # TODO raise proper exception
            raise Exception("DD client not registered") from None

    @staticmethod
    def read_domain_description_file():
        description_file = open(Configuration().DOMAIN_DESCRIPTION_FILE, "r")
        return description_file.read()


class DomainInformationManager(object):

    def __init__(self):
        self._fc_digest = None

    def start(self):

        # load static informations from file
        ResourceDescription().loadFile(Configuration().DOMAIN_DESCRIPTION_FILE)

        # get capabilities informations from controller
        ResourceDescription().clear_functional_capabilities()

        functional_capabilities = NetManager().get_apps_capabilities()
        self._fc_digest = self._calculate_capabilities_digest(functional_capabilities)
        for functional_capability in functional_capabilities:
            ResourceDescription().add_functional_capability(functional_capability)

        # save new file
        ResourceDescription().saveFile()

        # start dd_client
        logging.info("Starting doubledecker client...")
        Messaging().publish_domain_description()

        # periodically check for updates
        while Messaging().working_thread.isAlive():
            time.sleep(5)
            # get current capabilities from controller
            functional_capabilities = NetManager().get_apps_capabilities()
            # check if there are changes
            new_digest = self._calculate_capabilities_digest(functional_capabilities)
            if new_digest != self._fc_digest:
                logging.info("Domain information changed!")
                self._fc_digest = new_digest
                # update description with new capabilities
                ResourceDescription().clear_functional_capabilities()
                for functional_capability in functional_capabilities:
                    ResourceDescription().add_functional_capability(functional_capability)
                # save new file
                ResourceDescription().saveFile()
                # send updated domain informations
                Messaging().publish_domain_description()

    @staticmethod
    def _calculate_capabilities_digest(functional_capabilities):
        fc_list = []
        for fc in functional_capabilities:
            fc_list.append(fc.get_dict())

        data_md5 = hashlib.md5(json.dumps(fc_list, sort_keys=True).encode('utf-8')).hexdigest()
        return data_md5