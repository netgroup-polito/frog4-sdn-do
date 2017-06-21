import json

from do_core.config import Configuration
from do_core.rest_modules.config_service.rest import ConfigServiceRest

initial_configuration_file = 'initial_configuration.json'


class ConfigManager:

    def __init__(self, user_id, graph_id, nf_id):

        self.cs_endpoint = Configuration().CONFIG_SERVICE_ENDPOINT
        self.user_id = user_id
        self.graph_id = graph_id
        self.nf_id = nf_id

    def push_initial_configuration(self):
        config = self.fetch_initial_configuration()
        self.push_configuration(config)

    def fetch_initial_configuration(self):
        json_data = ConfigServiceRest().get_file(self.cs_endpoint, self.user_id, self.graph_id, self.nf_id,
                                                 initial_configuration_file)
        return json.loads(json_data)

    def push_configuration(self, config):
        ConfigServiceRest().push_config(self.cs_endpoint, self.user_id, self.graph_id, self.nf_id, json.dumps(config))
