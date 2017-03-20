import logging

from flask import request, jsonify
from flask_restplus import Resource

from orchestrator_core.api.api import api
from orchestrator_core.nffg_manager import NFFG_Manager
from orchestrator_core.userAuthentication import UserAuthentication
from orchestrator_core.exception import unauthorizedRequest, UserNotFound, VNFRepositoryError


template_ns = api.namespace('template', 'Template Resource')


class TemplateAPI(object):

    def get(self, image_id):
        pass


@template_ns.route('/location/<template_name>', methods=['GET'])
@api.doc(responses={404: 'Template not found'})
class TemplateLocationResource(Resource):

    @template_ns.param("template_name", "Template to be retrieved", "path", type="string", required=True)
    @template_ns.param("X-Auth-User", "Username", "header", type="string", required=True)
    @template_ns.param("X-Auth-Pass", "Password", "header", type="string", required=True)
    @template_ns.param("X-Auth-Tenant", "Tenant", "header", type="string", required=True)
    @template_ns.response(200, 'Template retrieved.')
    @template_ns.response(401, 'Unauthorized.')
    @template_ns.response(500, 'Internal Error.')
    def get(self, template_name):
        """
        Get the NF template
        """
        try:
            UserAuthentication().authenticateUserFromRESTRequest(request)
            return jsonify((NFFG_Manager().getTemplate(template_name).getDict()))
        except (unauthorizedRequest, UserNotFound) as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return "Unauthorized", 401
        except FileNotFoundError as err:
            return "Template not found", 404
        except VNFRepositoryError as err:
            return "VNFRepositoryError: Template not found or incorrect VNF-Repository configuration", 404
        except Exception as err:
            logging.exception(err)
            return "Contact the admin " + str(err), 500
