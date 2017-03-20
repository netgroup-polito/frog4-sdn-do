import logging
import requests
import json

from flask import request, Response
from flask_restplus import Resource
from sqlalchemy.orm.exc import NoResultFound

from nffg_library.nffg import NF_FG
from nffg_library.validator import ValidateNF_FG
from orchestrator_core.api.api import api
from orchestrator_core.controller import UpperLayerOrchestratorController
from orchestrator_core.userAuthentication import UserAuthentication
from orchestrator_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, UserNotFound, \
    VNFRepositoryError, NoFunctionalCapabilityFound, FunctionalCapabilityAlreadyInUse, \
    FeasibleDomainNotFoundForNFFGElement, FeasibleSolutionNotFoundForNFFG, GraphError, IncoherentDomainInformation, \
    UnsupportedLabelingMethod
from nffg_library.exception import NF_FGValidationError

nffg_ns = api.namespace('NF-FG', 'NFFG Resource')


@nffg_ns.route('/<nffg_id>', methods=['GET', 'DELETE'])
@nffg_ns.route('/', defaults={'nffg_id': None}, methods=['GET', 'PUT'])
@api.doc(responses={404: 'Graph not found'})
class NFFGResource(Resource):

    counter = 1

    @nffg_ns.param("nffg_id", "Graph ID to be deleted", "path", type="string", required=True)
    @nffg_ns.param("X-Auth-User", "Username", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Pass", "Password", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Tenant", "Tenant", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph deleted.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def delete(self, nffg_id):
        """
        Delete a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            controller = UpperLayerOrchestratorController(user_data)
            controller.delete(nffg_id)

            return "Session deleted"

        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return "EXCEPTION - NoResultFound", 404
        except requests.HTTPError as err:
            logging.exception(err)
            return str(err), 500
        except sessionNotFound as err:
            logging.exception(err.message)
            return err.message, 404
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return "Unauthorized", 401
        except Exception as err:
            logging.exception(err)
            return "Contact the admin: " + str(err), 500

    @nffg_ns.param("nffg_id", "Graph ID to be retrieved", "path", type="string", required=False)
    @nffg_ns.param("X-Auth-User", "Username", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Pass", "Password", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Tenant", "Tenant", "header", type="string", required=True)
    @nffg_ns.response(200, 'Graph retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id=None):
        """
        Returns an already deployed graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            controller = UpperLayerOrchestratorController(user_data)
            resp = Response(response=controller.get(nffg_id), status=200, mimetype="application/json")
            return resp

        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return "EXCEPTION - NoResultFound", 404
        except requests.HTTPError as err:
            logging.exception(err)
            return str(err), 500
        except requests.ConnectionError as err:
            logging.exception(err)
            return str(err), 500
        except sessionNotFound as err:
            logging.exception(err.message)
            return err.message, 404
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return "Unauthorized", 401
        except Exception as err:
            logging.exception(err)
            return "Contact the admin: " + str(err), 500

    @nffg_ns.param("X-Auth-User", "Username", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Pass", "Password", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Tenant", "Tenant", "header", type="string", required=True)
    @nffg_ns.param("nffg", "Graph to be deployed", "body", type="string", required=True)
    @nffg_ns.response(202, 'Graph correctly deployed.')
    @nffg_ns.response(400, 'Bad request.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(409, 'The graph is valid but does not have a feasible deployment in the current network.')
    @nffg_ns.response(500, 'Internal Error.')
    def put(self):
        """
        Deploy a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            nffg_dict = json.loads(request.data.decode())
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)

            controller = UpperLayerOrchestratorController(user_data, self.counter)
            response = controller.put(nffg)
            self.counter += 1

            return response, 202

        except wrongRequest as err:
            logging.exception(err)
            return "Bad Request", 400
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return "Unauthorized", 401
        except NF_FGValidationError as err:
            logging.exception(err)
            return "NF-FG Validation Error: " + err.message, 400
        except requests.HTTPError as err:
            logging.exception(err)
            return str(err), 500
        except requests.ConnectionError as err:
            logging.exception(err)
            return str(err), 500
        except VNFRepositoryError as err:
            return err.message, 500
        except GraphError as err:
            return err.message, 400
        except NoFunctionalCapabilityFound as err:
            return err.message, 400
        except FunctionalCapabilityAlreadyInUse as err:
            return err.message, 400
        except FeasibleDomainNotFoundForNFFGElement as err:
            return err.message, 409
        except FeasibleSolutionNotFoundForNFFG as err:
            return err.message, 409
        except IncoherentDomainInformation as err:
            return err.message, 500
        except UnsupportedLabelingMethod as err:
            return err.message, 500
        except Exception as err:
            logging.exception(err)
            return "Contact the admin: " + str(err), 500


@nffg_ns.route('/status/<nffg_id>', methods=['GET'])
@api.doc(responses={404: 'Graph not found'})
class NFFGStatusResource(Resource):

    @nffg_ns.param("nffg_id", "Graph ID to be retrieved", "path", type="string", required=True)
    @nffg_ns.param("X-Auth-User", "Username", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Pass", "Password", "header", type="string", required=True)
    @nffg_ns.param("X-Auth-Tenant", "Tenant", "header", type="string", required=True)
    @nffg_ns.response(200, 'Status correctly retrieved.')
    @nffg_ns.response(401, 'Unauthorized.')
    @nffg_ns.response(500, 'Internal Error.')
    def get(self, nffg_id):
        """
        Get the status of a graph
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)

            controller = UpperLayerOrchestratorController(user_data)
            resp = Response(response=controller.get_status(nffg_id), status=200, mimetype="application/json")
            return resp

        except NoResultFound:
            logging.exception("EXCEPTION - NoResultFound")
            return "EXCEPTION - NoResultFound", 404
        except requests.HTTPError as err:
            logging.exception(err)
            return str(err), 500
        except sessionNotFound as err:
            logging.exception(err.message)
            return err.message, 404
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return "Unauthorized", 401
        except Exception as err:
            logging.exception(err)
            return "Contact the admin: " + str(err), 500
