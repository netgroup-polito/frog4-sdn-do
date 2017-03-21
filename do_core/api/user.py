"""
Created on Mar 21, 2016

@author: gabrielecastellano
"""

import logging
import requests
import json

from flask import request
from flask_restplus import Resource, fields
from sqlalchemy.orm.exc import NoResultFound

from do_core.api.api import api
from do_core.user_authentication import UserAuthentication
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, UserNotFound, TenantNotFound, \
    UserTokenExpired


login_ns = api.namespace('login', 'Login Resource')
login_schema = login_ns.model('Login', {
    'username': fields.String(description="Username", type="string", required=True),
    'password': fields.String(description="Password", type="string", required=True)
})


@login_ns.route('', methods=['POST', 'HEAD'])
class LoginResource(Resource):

    @login_ns.expect(login_schema)
    @login_ns.response(200, 'Login successfully performed.')
    @login_ns.response(400, 'Bad request.')
    @login_ns.response(401, 'Login unauthorized.')
    @login_ns.response(500, 'Internal Error.')
    def post(self):
        """
        Perform the login through the credentials, returning the user token
        """
        try:
            payload = None
            request_body = request.data.decode('utf-8')
            if len(request_body) > 0:
                payload = json.loads(request_body, 'utf-8')

            userdata = UserAuthentication().authenticateUserFromRESTRequest(request, payload)

            return userdata.token, 200, {'Content-Type': 'application/token'}

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

    @login_ns.param("X-Auth-Token", "Authentication token", "header", type="string", required=True)
    @login_ns.param("prova", "prova", "header", type="string", required=True)
    @login_ns.response(200, 'Token is valid.')
    @login_ns.response(400, 'Bad request.')
    @login_ns.response(401, 'Login unauthorized.')
    @login_ns.response(500, 'Internal Error.')
    def head(self):
        """
        Checks the validity of the given token
        """
        try:
            token = request.headers.get("X-Auth-Token")

            if token is not None:
                UserAuthentication().authenticateUserFromToken(token)
            else:
                raise wrongRequest('Wrong authentication request: expected X-Auth-Token in the request header')

            return "Token is valid", 200

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
