import os
os.environ.setdefault("FROG4_SDN_DO_CONF", "config/script-config.ini")
import logging

from do_core.config import Configuration
from do_core.user_authentication import UserAuthentication
from do_core.do import DO

from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG


Configuration().log_configuration()

try:
    user_data = UserAuthentication().authenticateUserFromCredentials('admin', 'admin', 'admin_tenant')
    nffg_id = '123'

    nc_do = DO(user_data)
    nc_do.NFFG_Delete(nffg_id)

except Exception as err:
    logging.exception(err)
