'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''

import logging, json, requests
from flask import request, jsonify, Response
from sqlalchemy.orm.exc import NoResultFound

# Orchestrator Core
from do_core.user_authentication import UserAuthentication
from do_core.do import DO
from do_core.netmanager import NetManager
from do_core.config import Configuration

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG
from nffg_library.exception import NF_FGValidationError

# Exceptions
from do_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, NffgUselessInformations,\
    UserNotFound, TenantNotFound, UserTokenExpired, GraphError
from flask.views import MethodView


"""
class DO_REST_Base(object):
    '''
    Every response must be in json format and must have the following fields:
    - 'title' (e.g. "202 Accepted")
    - 'message' (e.g. "Graph 977 succesfully processed.")
    Additional fields should be used to send the requested data (e.g. nf-fg, status, user-data).
    
    All the classess "DO_REST_*" must inherit this class.
    This class contains:
        - common json response creator "_json_response"
        - common exception handlers "__except_*"
    '''
    
    def _json_response(self, http_status, message, status=None, nffg=None, userdata=None, topology=None):
        
        if status is not None:
            #response_json['status'] = status
            return status
        if nffg is not None:
            #response_json['nf-fg'] = nffg
            return nffg
        if userdata is not None:
            #response_json['user-data'] = userdata
            return userdata
        if topology is not None:
            #response_json['topology'] = topology
            return topology
        if message is None:
            return None
        
        response_json = {}
        response_json['title'] = http_status
        response_json['description'] = message
        return json.dumps(response_json)
    
    
    def __http_error(self, response,falcon_status_code, message):
        response.body = message
        response.status = falcon_status_code
        #raise falconHTTPError(falcon_status_code,falcon_status_code,message)
        
    
    '''
    Section: "Common Exception Handlers"
    '''
    
    def __get_exception_message(self,ex):
        if hasattr(ex, "args"): #and ex.args[0] is not None:
            return str(ex) #ex.args[0]
        elif hasattr(ex, "message") and ex.message is not None:
            return ex.message
        else:
            return "Unknown exception message"
        
    
    def _except_BadRequest(self, response, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        self.__http_error(response,falconStatusCodes.HTTP_400,message)

    def _except_unauthenticatedRequest(self, response, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        self.__http_error(response,falconStatusCodes.HTTP_401,message)
    
    def _except_NotAcceptable(self, response, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        self.__http_error(response,falconStatusCodes.HTTP_406,message)
    
    def _except_NotFound(self, response, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        self.__http_error(response,falconStatusCodes.HTTP_404,message)
    
    def _except_unauthorizedRequest(self,response,ex,request):
        username_string = ""
        if(request.get_header("X-Auth-User") is not None):
            username_string = " from user "+request.get_header("X-Auth-User")
        logging.error("Unauthorized access attempt"+username_string+".")
        message = self.__get_exception_message(ex)
        self.__http_error(response,falconStatusCodes.HTTP_401,message)
    
    def _except_requests_HTTPError(self,response,ex):
        logging.error(ex.response.text)
        if ex.response.status_code is not None:
            message = ex.response.status_code+" - "
            message += self.__get_exception_message(ex)
            self.__http_error(response,falconStatusCodes.HTTP_500,message)
        raise ex

    def _except_standardException(self,response,ex):
        message = self.__get_exception_message(ex)
        logging.exception(ex) #unique case which uses logging.exception
        self.__http_error(response,falconStatusCodes.HTTP_500,message)
"""


class DO_REST_NFFG_GPUD(MethodView):
    #GPUD = "Get Put Update Delete" 
    
    def put(self, nffg_id):
        """
        Put a graph
        Deploy a graph
        ---
        tags:
          - NF-FG
        parameters:
          - name: nffg_id
            in: path
            description: ID of the graph
            type: string
            required: true       
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
          - name: NF-FG
            in: body
            description: Graph to be deployed
            required: true
            schema:
                type: string
        responses:
          202:
            description: Graph correctly deployed  
          400:
            description: Bad request                  
          401:
            description: Unauthorized
          404:
            description: No results
          406:
            description: Not acceptable      
          500:
            description: Internal Error
        """
        try:
            user_data = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            request_body = request.data.decode('utf-8')
            nffg_dict = json.loads(request_body, 'utf-8')
            
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)
            nffg.id = nffg_id

            nc_do = DO(user_data)
            nc_do.NFFG_Validate(nffg)
            nc_do.NFFG_Put(nffg)
    
            return "Graph correctly deployed", 202
        
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

    def delete(self, nffg_id):
        """
        Delete a graph
        ---
        tags:
          - NF-FG   
        parameters:
          - name: nffg_id
            in: path
            description: Graph ID to be deleted
            required: true
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string            
        responses:
          200:
            description: Graph deleted
          400:
            description: Bad request                  
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """          
        try:
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            NCDO = DO(userdata)
            
            NCDO.NFFG_Delete(nffg_id)
            
            return ("Session deleted")

        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)    
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)             
        
        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return ("UserNotFound", 404)
        except TenantNotFound as err:
            logging.exception(err)
            return ("TenantNotFound", 404)
        except NoResultFound as err:
            logging.exception(err)
            return ("NoResultFound", 404)
        except sessionNotFound as err:
            logging.exception(err)
            return ("sessionNotFound", 404)
        
        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)            
        except Exception as err:
            logging.exception(err)
            return (str(err), 500)

    def get(self, nffg_id=None):
        """
        Get a graph
        Returns an already deployed graph
        ---
        tags:
          - NF-FG
        produces:
          - application/json          
        parameters:
          - name: nffg_id
            in: path
            description: Graph ID to be retrieved
            required: true
            type: string            
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string            
        responses:
          200:
            description: Graph retrieved
          400:
            description: Bad request                  
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """        
        try:
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            NCDO = DO(userdata)

            if nffg_id is None:
                # return all NFFGs
                resp = Response(response=json.dumps(NCDO.NFFG_Get_All()), status=200, mimetype="application/json")
            else:
                resp = Response(response=NCDO.NFFG_Get(nffg_id).getJSON(), status=200, mimetype="application/json")
            return resp            
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)    
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)   
        
        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return ("UserNotFound", 404)
        except TenantNotFound as err:
            logging.exception(err)
            return ("TenantNotFound", 404)
        except NoResultFound as err:
            logging.exception(err)
            return ("NoResultFound", 404)
        except sessionNotFound as err:
            logging.exception(err)
            return ("sessionNotFound", 404)
        
        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)            
        except Exception as err:
            logging.exception(err)
            return (str(err), 500)


class DO_REST_NFFG_Status(MethodView):
    def get(self, nffg_id):
        """
        Get the status of a graph
        ---
        tags:
          - NF-FG
        produces:
          - application/json             
        parameters:
          - name: nffg_id
            in: path
            description: Graph ID to be retrieved
            type: string            
            required: true
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
                    
        responses:
          200:
            description: Status correctly retrieved
          400:
            description: Bad request                
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """            
        try :
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            NCDO = DO(userdata)
            
            status,percentage = NCDO.NFFG_Status(nffg_id)
            status_json = {}
            status_json['status'] = status 
            status_json['percentage_completed'] = percentage
            
            if status=='initialization' or status=='updating':
                status_json['status'] = 'in_progress'
            
            return jsonify(status_json) #self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" found.", status=json.dumps(status) )
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)    
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)   
        
        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return ("UserNotFound", 404)
        except TenantNotFound as err:
            logging.exception(err)
            return ("TenantNotFound", 404)
        except NoResultFound as err:
            logging.exception(err)
            return ("NoResultFound", 404)
        except sessionNotFound as err:
            logging.exception(err)
            return ("sessionNotFound", 404)
        
        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)            
        except Exception as err:
            logging.exception(err)
            return (str(err), 500)


class DO_UserAuthentication(MethodView):
    def post(self):
        """
        Perform the login
        Given the credentials it returns the token associated to that user
        ---
        tags:
          - NF-FG
        parameters:
          - in: body
            name: body
            schema:
              id: login
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  description:  username
                password:
                  type: string
                  description: password

        responses:
          200:
            description: Login successfully performed
          400:
            description: Bad request                     
          401:
           description: Login failed
          500:
            description: Internal Error                
        """        
        try:
            payload = None
            request_body = request.data.decode('utf-8')
            if len(request_body)>0:
                payload = json.loads(request_body, 'utf-8')
            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request, payload)
            
            return userdata.token, 200, {'Content-Type': 'application/token'} #userdata.getResponseJSON() #self._json_response(falcon.HTTP_200, "User "+userdata.username+" found.", userdata=userdata.getResponseJSON())
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
                
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
                
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)

        # NFFG validation - raised by json.loads()
        except ValueError as err:
            logging.exception(err)
            return ("ValueError", 406)
        
        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return ("UserNotFound", 404)
        except TenantNotFound as err:
            logging.exception(err)
            return ("TenantNotFound", 404)
        except NoResultFound as err:
            logging.exception(err)
            return ("NoResultFound", 404)
        except sessionNotFound as err:
            logging.exception(err)
            return ("sessionNotFound", 404)
        
        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)            
        except Exception as err:
            logging.exception(err)
            return (str(err), 500)
    
    
    def head(self):
        """
        Test a token
        It checks the validity of the given token
        ---
        tags:
          - NF-FG
        parameters:
          - name: X-Auth-Token
            in: header
            description: Authentication token to be tested
            required: true
            type: string

        responses:
          200:
            description: Token is valid
          400:
            description: Bad request                     
          401:
           description: Login failed
          500:
            description: Internal Error                
        """          
        try:
            token = request.headers.get("X-Auth-Token")
        
            if token is not None:
                UserAuthentication().authenticateUserFromToken(token)
            else:
                raise wrongRequest('Wrong authentication request: expected X-Auth-Token in the request header')
            
            return ("Token is valid")
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
                
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
                
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)

        # NFFG validation - raised by json.loads()
        except ValueError as err:
            logging.exception(err)
            return ("ValueError", 406)
        
        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return ("UserNotFound", 404)
        except TenantNotFound as err:
            logging.exception(err)
            return ("TenantNotFound", 404)
        except NoResultFound as err:
            logging.exception(err)
            return ("NoResultFound", 404)
        except sessionNotFound as err:
            logging.exception(err)
            return ("sessionNotFound", 404)
        
        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)            
        except Exception as err:
            logging.exception(err)
            return (str(err), 500)


class DO_NetworkTopology(MethodView):
    def get(self):
        """
        Get the network topology
        ---
        tags:
          - network topology
        produces:
          - application/json             
        parameters:
          - name: X-Auth-Token
            in: header
            description: Authentication token
            required: true
            type: string
                    
        responses:
          200:
            description: Topology correctly retrieved
          400:
            description: Bad request                
          401:
            description: Unauthorized
          404:
            description: Graph not found
          500:
            description: Internal Error
        """            
        try :
            UserAuthentication().authenticateUserFromRESTRequest(request)
            
            ng = NetManager()
            
            return jsonify(ng.getNetworkTopology()) #self._json_response(falcon.HTTP_200, "Network topology", topology=json.dumps(ng.getNetworkTopology()))
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            logging.exception(err)
            return ("Bad Request", 400)
                
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            if request.headers.get("X-Auth-User") is not None:
                logging.debug("Unauthorized access attempt from user "+request.headers.get("X-Auth-User"))
            logging.debug(err.message)
            return ("Unauthorized", 401)
                
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            logging.exception(err)
            return (err.message, 401)
        
        # No Results
        except UserNotFound as err:
            logging.exception(err)
            return ("UserNotFound", 404)
        except TenantNotFound as err:
            logging.exception(err)
            return ("TenantNotFound", 404)
        except NoResultFound as err:
            logging.exception(err)
            return ("NoResultFound", 404)
        except sessionNotFound as err:
            logging.exception(err)
            return ("sessionNotFound", 404)
        
        # Other errors
        except requests.HTTPError as err:
            logging.exception(err)
            return (str(err), 500)            
        except Exception as err:
            logging.exception(err)
            return (str(err), 500)
