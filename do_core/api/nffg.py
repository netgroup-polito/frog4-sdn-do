"""
Created on Mar 20, 2016

@author: gabrielecastellano
"""

import logging
import requests
import json

from flask import request, jsonify, Response
from flask_restplus import Resource
from sqlalchemy.orm.exc import NoResultFound

from nffg_library.nffg import NF_FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.exception import NF_FGValidationError

from do_core.api.api import api
from do_core.user_authentication import UserAuthentication
from do_core.do import DO

from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, NffgUselessInformations, \
    UserNotFound, TenantNotFound, UserTokenExpired, GraphError, NoPathBetweenSwitches, NoGraphFound

nffg_ns = api.namespace('NF-FG', 'NFFG Resource')


@nffg_ns.route('/<nffg_id>', methods=['GET', 'DELETE', 'PUT'],
               doc={'params': {'nffg_id': {'description': 'The graph ID', 'in': 'path'}}})
@nffg_ns.route('/', methods=['GET', 'POST'])
class NFFGResource(Resource):

    @nffg_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @nffg_ns.param("nffg", "Graph to be deployed", "body", type="string", required=True)
    @nffg_ns.response(201, 'Graph correctly deployed.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(404, 'No result.')
    @nffg_ns.response(406, 'Not acceptable.')
    @nffg_ns.response(500, 'Internal Error.')
    def post(self):
        """
        Create a New Network Functions Forwarding Graph
        Deploy a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            request_body = request.data.decode('utf-8')
            nffg_dict = json.loads(request_body, 'utf-8')

            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)

            nc_do = DO(user_data)
            nc_do.validate_nffg(nffg)
            resp = Response(response=nc_do.post_nffg(nffg), status=201, mimetype="application/json")
            return resp

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

        # NFFG validation - raised by json.loads()
        except ValueError as err:
            logging.exception(err)
            return "ValueError", 406

        # NFFG validation - raised by ValidateNF_FG().validate
        except NF_FGValidationError as err:
            logging.exception(err)
            return "NF_FGValidationError", 406

        # NFFG validation - raised by the class DO()
        except GraphError as err:
            logging.exception(err)
            return "GraphError", 406

        # Custom NFFG sub-validation - raised by DO().NFFG_Validate
        except NffgUselessInformations as err:
            logging.exception(err)
            return err.message, 406

        # Topology errors
        except NoPathBetweenSwitches as err:
            logging.exception(err)
            return err.message, 422

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

    @nffg_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @nffg_ns.param("nffg", "Graph to be updated", "body", type="string", required=True)
    @nffg_ns.response(202, 'Graph correctly updated.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(404, 'No result.')
    @nffg_ns.response(406, 'Not acceptable.')
    @nffg_ns.response(500, 'Internal Error.')
    def put(self, nffg_id):
        """
        Update a Network Functions Forwarding Graph
        Update a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            request_body = request.data.decode('utf-8')
            nffg_dict = json.loads(request_body, 'utf-8')

            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)

            nc_do = DO(user_data)
            nc_do.validate_nffg(nffg)
            nc_do.put_nffg(nffg, nffg_id)
            resp = Response(response=None, status=202, mimetype="application/json")
            return resp

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

        # NFFG validation - raised by json.loads()
        except ValueError as err:
            logging.exception(err)
            return "ValueError", 406

        # NFFG validation - raised by ValidateNF_FG().validate
        except NF_FGValidationError as err:
            logging.exception(err)
            return "NF_FGValidationError", 406

        # NFFG validation - raised by the class DO()
        except GraphError as err:
            logging.exception(err)
            return "GraphError", 406

        # Custom NFFG sub-validation - raised by DO().NFFG_Validate
        except NffgUselessInformations as err:
            logging.exception(err)
            return err.message, 406

        # Topology errors
        except NoPathBetweenSwitches as err:
            logging.exception(err)
            return err.message, 422

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
        except NoGraphFound as err:
            logging.exception(err)
            return err.message, 404

        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return str(err), 500
        except Exception as err:
            logging.exception(err)
            return str(err), 500

    @nffg_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph deleted.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(404, 'Graph not found.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def delete(self, nffg_id):
        """
        Delete a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            do = DO(user_data)

            do.delete_nffg(nffg_id)

            return "Session deleted", 200

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

    @nffg_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph retrieved.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(404, 'Graph not found.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id=None):
        """
        Returns an already deployed graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            do = DO(user_data)

            if nffg_id is None:
                # return all NFFGs
                resp = Response(response=json.dumps(do.get_nffgs()), status=200, mimetype="application/json")
            else:
                resp = Response(response=do.get_nffg(nffg_id).getJSON(), status=200, mimetype="application/json")
            return resp

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


@nffg_ns.route('/status/<nffg_id>', methods=['GET'], doc={'params': {'nffg_id': {'description': 'The graph ID'}}})
@api.doc(responses={404: 'Graph not found'})
class NFFGStatusResource(Resource):

    @nffg_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @nffg_ns.response(200, 'Status correctly retrieved.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(404, 'Graph not found.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id):
        """
        Get the status of a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            do = DO(user_data)

            status, percentage = do.nffg_status(nffg_id)
            status_json = dict()
            status_json['status'] = status
            status_json['percentage_completed'] = percentage

            if status == 'initialization' or status == 'updating':
                status_json['status'] = 'in_progress'

            return jsonify(status_json)

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
