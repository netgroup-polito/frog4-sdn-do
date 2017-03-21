"""
Created on Mar 20, 2016

@author: gabrielecastellano
"""

import logging
import requests

from flask import request, jsonify
from flask_restplus import Resource
from sqlalchemy.orm.exc import NoResultFound

from do_core.api.api import api
from do_core.netmanager import NetManager
from do_core.user_authentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, UserNotFound, TenantNotFound, \
    UserTokenExpired


topology_ns = api.namespace('topology', 'Network Topology Resource')


class Network(object):

    def get(self, image_id):
        pass


@topology_ns.route('', methods=['GET'])
class NetworkTopologyResource(Resource):

    @topology_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @topology_ns.response(200, 'Topology correctly retrieved.')
    @topology_ns.response(401, 'Unauthorized.')
    @topology_ns.response(500, 'Internal Error.')
    def get(self):
        """
        Get the network topology
        """
        try:
            UserAuthentication().authenticateUserFromRESTRequest(request)

            ng = NetManager()

            return jsonify(ng.getNetworkTopology())

        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return "Bad Request", 400

        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return "Unauthorized", 401

        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return err.message, 401

        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return "UserNotFound", 404
        except TenantNotFound as err:
            logging.exception(err)
            return "TenantNotFound", 404
        except NoResultFound as err:
            logging.exception(err)
            return "NoResultFound", 404
        except sessionNotFound as err:
            logging.exception(err)
            return "sessionNotFound", 404

        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return str(err), 500
        except Exception as err:
            logging.exception(err)
            return str(err), 500
