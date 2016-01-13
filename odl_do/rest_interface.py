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

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG
from nffg_library.exception import NF_FGValidationError

# Exceptions
from odl_do.exception import wrongRequest, unauthorizedRequest, sessionNotFound, NffgUselessInformations,\
    UserNotFound, TenantNotFound



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
    
    def _json_response(self, http_status, message, status=None, nffg=None, userdata=None):
        response_json = {}
        
        response_json['title'] = http_status
        response_json['message'] = message
        
        if status is not None:
            response_json['status'] = status
        if nffg is not None:
            response_json['nf-fg'] = nffg
        if userdata is not None:
            response_json['user-data'] = userdata

        return json.dumps(response_json)
        
    
    '''
    Section: "Common Exception Handlers"
    '''
    
    def __get_exception_message(self,ex):
        if hasattr(ex, "args") and ex.args[0] is not None:
            return ex.args[0]
        elif hasattr(ex, "message") and ex.message is not None:
            return ex.message
        else:
            return "Unknown exception message"
        
    
    def _except_BadRequest(self, prefix, ex):
        message = self.__get_exception_message(ex)
        logging.error(prefix+": "+message)
        #raise falcon.HTTPBadRequest('Bad Request',message)
        raise falconHTTPError(falconStatusCodes.HTTP_400,falconStatusCodes.HTTP_400,message)
    
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
        raise falconHTTPError(falconStatusCodes.HTTP_403,falconStatusCodes.HTTP_403,message)
    
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




 
class OpenDayLightDO_REST_NFFG_Put(OpenDayLightDO_REST_Base):
    
    def on_put(self, request, response):
        try:            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            nffg_dict = json.loads(request.stream.read().decode('utf-8'), 'utf-8')
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)
            
            odlDO = OpenDayLightDO(userdata)
            odlDO.NFFG_Validate(nffg)
            odlDO.NFFG_Put(nffg)
    
            response.body = self._json_response(falcon.HTTP_202, "Graph "+nffg.id+" succesfully processed.")
            response.status = falcon.HTTP_202
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
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
    
    



class OpenDayLightDO_REST_NFFG_Get_Delete(OpenDayLightDO_REST_Base):
    
    def on_delete(self, request, response, nffg_id):
        try :
            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlDO = OpenDayLightDO(userdata)
            
            odlDO.NFFG_Delete(nffg_id)
            
            response.body = self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" succesfully deleted.")
            response.status = falcon.HTTP_200

        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
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
            
            response.body = self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" found.", nffg=odlDO.NFFG_Get(nffg_id))
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
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

            response.body = self._json_response(falcon.HTTP_200, "Graph "+nffg_id+" found.", status=odlDO.NFFG_Status(nffg_id))
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
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
        try :
            print(request.uri)
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            response.body = self._json_response(falcon.HTTP_200, "User "+userdata.username+" found.", userdata=userdata.getResponseJSON())
            response.status = falcon.HTTP_200
        
        # User auth request - raised by UserAuthentication().authenticateUserFromRESTRequest
        except wrongRequest as err:
            self._except_BadRequest("wrongRequest",err)
        
        # User auth credentials - raised by UserAuthentication().authenticateUserFromRESTRequest
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        
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



