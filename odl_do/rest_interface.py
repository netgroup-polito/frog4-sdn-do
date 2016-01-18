'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''

import logging, json, requests, falcon
from falcon.http_error import HTTPError as falconHTTPError
import falcon.status_codes  as falconStatusCodes
from sqlalchemy.orm.exc import NoResultFound

# Orchestrator Core
from odl_do.user_authentication import UserAuthentication
from odl_do.opendaylight_do import OpenDayLightDO
from odl_do.netgraph import NetGraph
from odl_do.config import Configuration

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG
from nffg_library.exception import NF_FGValidationError

# Exceptions
from odl_do.exception import wrongRequest, unauthorizedRequest, sessionNotFound, NffgUselessInformations,\
    UserNotFound, TenantNotFound, UserTokenExpired



class OpenDayLightDO_REST_Base(object):
    '''
    Every response must be in json format and must have the following fields:
    - 'title' (e.g. "202 Accepted")
    - 'message' (e.g. "Graph 977 succesfully processed.")
    Additional fields should be used to send the requested data (e.g. nf-fg, status, user-data).
    
    All the classess "OpenDayLightDO_REST_*" must inherit this class.
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
    
    
    def _json_response_for_auth(self, http_status, message, userdata):
        #response_json = {}

        return userdata
        
    
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
        
    
    def _except_BadRequest(self, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        raise falconHTTPError(falconStatusCodes.HTTP_400,falconStatusCodes.HTTP_400,message)

    def _except_unauthenticatedRequest(self, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        raise falconHTTPError(falconStatusCodes.HTTP_401,falconStatusCodes.HTTP_401,message)
    
    def _except_NotAcceptable(self, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        raise falconHTTPError(falconStatusCodes.HTTP_406,falconStatusCodes.HTTP_406,message)
    
    def _except_NotFound(self, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        raise falconHTTPError(falconStatusCodes.HTTP_404,falconStatusCodes.HTTP_404,message)
    
    def _except_unauthorizedRequest(self,ex,request):
        username_string = ""
        if(request.get_header("X-Auth-User") is not None):
            username_string = " from user "+request.get_header("X-Auth-User")
        logging.error("Unauthorized access attempt"+username_string+".")
        message = self.__get_exception_message(ex)
        raise falconHTTPError(falconStatusCodes.HTTP_401,falconStatusCodes.HTTP_401,message)
    
    def _except_requests_HTTPError(self,ex):
        logging.error(ex.response.text)
        if ex.response.status_code is not None:
            message = ex.response.status_code+" - "
            message += self.__get_exception_message(ex)
            raise falconHTTPError(falconStatusCodes.HTTP_500,falconStatusCodes.HTTP_500,message)
        raise ex

    def _except_standardException(self,ex):
        message = self.__get_exception_message(ex)
        logging.exception(ex) #unique case which uses logging.exception
        raise falconHTTPError(falconStatusCodes.HTTP_500,'500 - Unexpected Internal Server Error',message)



class OpenDayLightDO_REST_NFFG_GPUD(OpenDayLightDO_REST_Base):
    #GPUD = "Get Put Update Delete" 
    
    def on_put(self, request, response, nffg_id):
        try:            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            request_body = request.stream.read().decode('utf-8')
            nffg_dict = json.loads(request_body, 'utf-8')
            
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)
            
            odlDO = OpenDayLightDO(userdata)
            odlDO.NFFG_Validate(nffg)
            odlDO.NFFG_Put(nffg)
    
            response.body = None #self._json_response(falcon.HTTP_202, "Graph "+nffg.id+" succesfully processed.")
            response.status = falcon.HTTP_202
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # NFFG validation - raised by json.loads()
        except ValueError as err:
            self._except_NotAcceptable("ValueError",err)
        
        # NFFG validation - raised by ValidateNF_FG().validate
        except NF_FGValidationError as err:
            self._except_NotAcceptable("NF_FGValidationError",err)
        
        # Custom NFFG sub-validation - raised by OpenDayLightDO().NFFG_Validate
        except NffgUselessInformations as err:
            self._except_NotAcceptable("NffgUselessInformations",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound as err:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)
    

    
    def on_delete(self, request, response, nffg_id):
        try :
            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlDO = OpenDayLightDO(userdata)
            
            odlDO.NFFG_Delete(nffg_id)
            
            response.body = None #self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" succesfully deleted.")
            response.status = falcon.HTTP_200

        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)

    
    
    def on_get(self, request, response, nffg_id):
        try :
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlDO = OpenDayLightDO(userdata)
            
            response.body = odlDO.NFFG_Get(nffg_id) #self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" found.", nffg=odlDO.NFFG_Get(nffg_id))
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound as err:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)





class OpenDayLightDO_REST_NFFG_Status(OpenDayLightDO_REST_Base):
    def on_get(self, request, response, nffg_id):
        try :
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlDO = OpenDayLightDO(userdata)
            
            status = odlDO.NFFG_Status(nffg_id)
            status_json = {}
            status_json['status'] = status 
            
            response.body = json.dumps(status_json) #self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" found.", status=json.dumps(status) )
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound as err:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)





class OpenDayLightDO_UserAuthentication(OpenDayLightDO_REST_Base):
    def on_post(self, request, response):
        try:
            payload = None
            request_body = request.stream.read().decode('utf-8')
            if len(request_body)>0:
                payload = json.loads(request_body, 'utf-8')
            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request, payload)
            
            response.body = userdata.getResponseJSON() #self._json_response(falcon.HTTP_200, "User "+userdata.username+" found.", userdata=userdata.getResponseJSON())
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # NFFG validation - raised by json.loads()
        except ValueError as err:
            self._except_NotAcceptable("ValueError",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound as err:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)
    
    
    
    def on_head(self, request, response):
        try:
            token = request.get_header("X-Auth-Token")
        
            if token is not None:
                UserAuthentication().authenticateUserFromToken(token)
            else:
                raise wrongRequest('Wrong authentication request: expected X-Auth-Token in the request header')
            
            response.body = None
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # NFFG validation - raised by json.loads()
        except ValueError as err:
            self._except_NotAcceptable("ValueError",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound as err:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)




class OpenDayLightDO_NetworkTopology(OpenDayLightDO_REST_Base):
    def on_get(self, request, response):
        try :
            UserAuthentication().authenticateUserFromRESTRequest(request)
            
            ng = NetGraph(Configuration().ODL_VERSION,
                          Configuration().ODL_ENDPOINT, 
                          Configuration().ODL_USERNAME, 
                          Configuration().ODL_PASSWORD)
            
            response.body = json.dumps(ng.getNetworkTopology()) #self._json_response(falcon.HTTP_200, "Network topology", topology=json.dumps(ng.getNetworkTopology()))
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except UserTokenExpired as err:
            self._except_unauthenticatedRequest("UserTokenExpired",err)
        
        # No Results
        except UserNotFound as err:
            self._except_NotFound("UserNotFound",err)
        except TenantNotFound as err:
            self._except_NotFound("TenantNotFound",err)
        except NoResultFound as err:
            self._except_NotFound("NoResultFound",err)
        except sessionNotFound as err:
            self._except_NotFound("sessionNotFound",err)
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)



