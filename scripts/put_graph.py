import os
os.environ.setdefault("FROG4_SDN_DO_CONF", "config/script-local-config.ini")
import logging
import json

from do_core.config import Configuration
from do_core.user_authentication import UserAuthentication
from do_core.do import DO

from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

Configuration().log_configuration()

try:

    user_data = UserAuthentication().authenticateUserFromCredentials('admin', 'qwerty', 'admin_tenant')
    nffg_id = '123'

    request_body = '{"forwarding-graph":{"name":"nat-graph","VNFs":[{"name":"nat","id":"00000001","vnf_template":"nat.json","ports":[{"name":"data-port","id":"USER:0"},{"name":"data-port","id":"WAN:0"}]}],"id":"3","end-points":[{"type":"vlan","vlan":{"vlan-id":"294","if-name":"s2-eth1","node-id":"of:0000000000000002"},"id":"00000001","name":"INGRESS"},{"type":"vlan","vlan":{"vlan-id":"294","if-name":"s3-eth1","node-id":"of:0000000000000003"},"id":"00000002","name":"INGRESS"}],"big-switch":{"flow-rules":[{"match":{"port_in":"endpoint:00000002"},"actions":[{"output_to_port":"vnf:00000001:WAN:0"}],"priority":40001,"id":"000000003"},{"match":{"port_in":"vnf:00000001:WAN:0"},"actions":[{"output_to_port":"endpoint:00000002"}],"priority":40001,"id":"000000004"},{"match":{"port_in":"endpoint:00000001"},"actions":[{"output_to_port":"vnf:00000001:USER:0"}],"priority":40001,"id":"000000007"},{"match":{"port_in":"vnf:00000001:USER:0"},"actions":[{"output_to_port":"endpoint:00000001"}],"priority":40001,"id":"000000008"}]}}}'
    nffg_dict = json.loads(request_body, 'utf-8')

    ValidateNF_FG().validate(nffg_dict)
    nffg = NF_FG()
    nffg.parseDict(nffg_dict)
    nffg.id = nffg_id

    nc_do = DO(user_data)
    nc_do.NFFG_Validate(nffg)
    nc_do.NFFG_Put(nffg)
except Exception as err:
    logging.exception(err)
