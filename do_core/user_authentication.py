'''
Created on 18 set 2015

@author: vida
@author: giacomoratta
'''

import hashlib, time, logging, json, binascii
from do_core.sql.user import User
from do_core.exception import unauthorizedRequest, wrongRequest, UserTokenExpired
from do_core.config import Configuration


class UserData(object):
    
    def __init__(self, user_id=None, username=None, tenant=None, email=None):
        self.user_id = user_id
        self.username = username
        self.tenant = tenant
        self.email = email
        self.token = None
        self.token_timestamp = None
    
    def setToken(self, token, timestamp):
        self.token = token
        self.token_timestamp = timestamp
    
    def getResponseJSON(self):
        obj = {}
        obj['user_id'] = self.user_id
        obj['token'] = self.token
        return json.dumps(obj)

# Used only in rest_interface.py and main1.py
# The two public functions must return a UserData object
class UserAuthentication(object):
    
    def __init__(self):
        self.token_expiration_time = int(Configuration().AUTH_TOKEN_EXPIRATION)
    
    def __getPasswordHash(self, password):
        pwdsha = hashlib.sha256() # sha512...len=64; sha256...len=32
        pwdsha.update(password.encode('utf-8'))
        return binascii.b2a_hex(pwdsha.digest()).decode('utf-8')
    
    def __isAnExpiredToken(self, token_timestamp):
        if token_timestamp is None:
            return True
        token_timestamp = int(token_timestamp)
        tt = int(time.time())
        return ( ( tt - token_timestamp) > self.token_expiration_time )

    def __getTimestamp(self):
        return time.time()

    def authenticateUserFromToken(self, token):
        '''
        Checks the user authentication by token.
        '''
        exception1 = unauthorizedRequest('Invalid authentication credentials')
        
        if token is None:
            raise exception1
        
        try:
            logging.info("Get user credentials and check token.")
            user = User().getUserByToken(token)
            logging.debug("Search for the user token "+str(token)+".")
            if user.token==token:
                if self.__isAnExpiredToken(user.token_timestamp)==False:
                    tenantName = User().getTenantName(user.tenant_id)
                    userobj = UserData(user.id, user.username, tenantName, user.mail)
                    userobj.setToken(user.token, user.token_timestamp)
                    logging.debug("Found user token "+str(token)+" still valid.")
                    return userobj
                else:
                    logging.debug("Found an expired user token "+str(token)+".")
                    raise UserTokenExpired("Token expired. You must authenticate again with user/pass")
            raise Exception
        except UserTokenExpired as ex:
            raise ex
        except Exception:
            logging.debug("User token "+str(token)+" not found.")
            raise exception1


    def authenticateUserFromCredentials(self, username, password, tenant):
        '''
        Checks the user authentication by username/password/tenant.
        '''
        exception1 = unauthorizedRequest('Invalid authentication credentials')
        
        if username is None or password is None: # or tenant is None:
            raise exception1
        
        logging.info("Get user credentials and check password.")
        user = User().getUserByUsername(username)
        
        # Check password
        pwdhash_check = self.__getPasswordHash(password)
        if user.pwdhash != pwdhash_check:
            logging.debug("Wrong password.")
            raise exception1
            
        # Check tenant
        tenantName = User().getTenantName(user.tenant_id)
        if tenant is not None and tenantName != tenant:
            logging.debug("Wrong tenant.")
            raise exception1
        
        userobj = UserData(user.id, user.username, tenantName, user.mail)
        
        logging.info("Check current token. Get a new token, if it is needed.")
        if user.token is None or self.__isAnExpiredToken(user.token_timestamp):
            token,token_timestamp = User().getNewToken(user.id)
            userobj.setToken(token, token_timestamp)
            User().setNewToken(user.id, token, token_timestamp)
            logging.debug("New token generated")
        else:
            userobj.setToken(user.token, user.token_timestamp)
            logging.debug("Current token is valid.")
        return userobj

    def authenticateUserFromRESTRequest(self, request, payload=None):
        '''
        Manages the authentication process via REST.
        Reads the header fields that starts with "X-Auth-" and 
        call the proper methods to check the user authentication.
        '''

        username = request.headers.get("X-Auth-User")
        password = request.headers.get("X-Auth-Pass")

        token = request.headers.get("X-Auth-Token")
        
        if token is not None:
            return self.authenticateUserFromToken(token)
        
        elif payload is not None and 'username' in payload.keys() and 'password' in payload.keys():
            return self.authenticateUserFromCredentials(payload['username'], payload['password'], None)
        
        elif username is not None and password is not None:  # and tenant is not None:
            return self.authenticateUserFromCredentials(username, password, None)
        
        raise wrongRequest('Wrong authentication request: send user/password or token')
