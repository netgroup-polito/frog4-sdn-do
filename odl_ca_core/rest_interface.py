'''
Created on Oct 1, 2014

@author: fabiomignini
@author: giacomoratta
'''

import logging, json, jsonschema, requests, falcon

from sqlalchemy.orm.exc import NoResultFound

# Orchestrator Core
from odl_ca_core.user_authentication import UserAuthentication
from odl_ca_core.opendaylight_ca import OpenDayLightCA

# NF-FG
from nffg_library.validator import ValidateNF_FG
from nffg_library.nffg import NF_FG

# Exceptions
from odl_ca_core.exception import wrongRequest, unauthorizedRequest, sessionNotFound, NffgUselessInformations




class OpenDayLightCA_REST_Base(object):
    '''
    All the classess "OpenDayLightCA_REST_*" must inherit this class.
    This class contains:
        - common exception handlers "_except_*"
    '''
    
    
    '''
    Section: "Common Exception Handlers"
    '''
    
    def _except_requests_HTTPError(self,ex):
        logging.exception(ex.response.text)
        if ex.response.status_code is not None:
            msg = ex.response.status_code+" - "
            if ex.message is not None:
                msg += ex.message
            raise falcon.HTTPInternalServerError('Falcon: Internal Server Error',msg)
        raise ex
    
    def _except_unauthorizedRequest(self,ex,request):
        username_string = ""
        if(request.get_header("X-Auth-User") is not None):
            username_string = " from user "+request.get_header("X-Auth-User")
        logging.debug("Unauthorized access attempt"+username_string+".")
        raise falcon.HTTPUnauthorized("Unauthorized", ex.message)

    def _except_standardException(self,ex,title=None):
        logging.exception(ex)
        if title is None:
            title = 'Contact the admin'
        title = title+'. '
        raise falcon.HTTPInternalServerError(title,ex.message)




 
class OpenDayLightCA_REST_NFFG(OpenDayLightCA_REST_Base):
    
    def on_put(self, request, response):
        try:
            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            nffg_dict = json.load(request.stream, 'utf-8')
            ValidateNF_FG().validate(nffg_dict)
            nffg = NF_FG()
            nffg.parseDict(nffg_dict)
            
            odlCA = OpenDayLightCA(userdata)
            odlCA.NFFG_Validate(nffg)
            odlCA.NFFG_Put(nffg)
    
            # TODO: write a json response
            response.body = "Graph "+nffg.id+" succesfully processed."
            response.status = falcon.HTTP_202
            
        # JSON format error
        except jsonschema.ValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request',err.message)
        
        # NFFG useless informations
        except NffgUselessInformations as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request',err.message)
        
        # Wrong request
        except wrongRequest as err:
            logging.exception(err)
            raise falcon.HTTPBadRequest("Bad Request", err.description)
        
        # Authorization
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
            
        # No Results
        except NoResultFound:
            logging.exception('Result Not found.')
            raise falcon.HTTPNotFound()
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)
    
    
    
    def on_delete(self, request, response, nffg_id):
        try :
            
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlCA = OpenDayLightCA(userdata)
            
            odlCA.NFFG_Delete(nffg_id)
            
            # TODO: write a json response
            response.body = "Graph "+nffg_id+" succesfully deleted."
            
        # JSON format error
        except jsonschema.ValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request',err.message)
        
        # Authorization
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
            
        # No Results
        except NoResultFound:
            logging.exception('Result Not found.')
            raise falcon.HTTPNotFound()
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)

    
    
    def on_get(self, request, response, nffg_id):
        try :
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlCA = OpenDayLightCA(userdata)
            
            # TODO: write a json response
            response.body = odlCA.NFFG_Get(nffg_id)
            response.status = falcon.HTTP_200
        
        # JSON format error
        except jsonschema.ValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request',err.message)
        
        # Authorization
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
            
        # No Results
        except NoResultFound:
            logging.exception('Result Not found.')
            raise falcon.HTTPNotFound()
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)





class OpenDayLightCA_REST_NFFGStatus(OpenDayLightCA_REST_Base):
    def on_get(self, request, response, nffg_id):
        try :
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            odlCA = OpenDayLightCA(userdata)
            
            # Writting a json response
            status_json = {}
            status_json['status'] = odlCA.NFFG_Status(nffg_id)
            
            response.body = json.dumps(status_json)
            response.status = falcon.HTTP_200
        
        # JSON format error
        except jsonschema.ValidationError as err:
            logging.exception(err.message)
            raise falcon.HTTPBadRequest('Bad Request',err.message)
        
        # Authorization
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
            
        # No Results
        except NoResultFound:
            logging.exception('Result Not found.')
            raise falcon.HTTPNotFound()
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)





class OpenDayLightCA_UserAuthentication(OpenDayLightCA_REST_Base):
    def on_post(self, request, response):
        try :
            userdata = UserAuthentication().authenticateUserFromRESTRequest(request)
            
            response.body = userdata.getResponseJSON()
            response.status = falcon.HTTP_200
        
        # Authorization
        except unauthorizedRequest as err:
            self._except_unauthorizedRequest(err,request)
        except wrongRequest as err:
            self._except_standardException(err,"Wrong authentication request")
        
        # No Results
        except NoResultFound:
            logging.exception('Result Not found.')
            raise falcon.HTTPNotFound()
        except sessionNotFound as err:
            logging.exception(err.message)
            raise falcon.HTTPNotFound()
        
        # Other errors
        except requests.HTTPError as err:
            self._except_requests_HTTPError(err)
        except Exception as ex:
            self._except_standardException(ex)



