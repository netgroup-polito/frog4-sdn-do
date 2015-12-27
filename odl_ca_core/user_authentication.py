'''
Created on 18 set 2015

@author: vida
@author: giacomoratta
'''

import hashlib, time, logging, json, binascii
from odl_ca_core.sql.user import User
from odl_ca_core.exception import unauthorizedRequest, wrongRequest
from odl_ca_core.config import Configuration



class UserData(object):
    
    def __init__(self, user_id=None, username=None, tenant=None, email=None):
        self.user_id = user_id
        self.username = username
        self.tenant = tenant
        self.email = email
        self.token = None
        self.token_timestamp = None
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
        conf = Configuration()
        conf.log_configuration()
        self.token_expiration_time = int(conf.AUTH_TOKEN_EXPIRATION)
    
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
        '''
        Timestamp:
            import time
            timestamp = time.time()
            print timestamp
            1355563265.81
        DateTime:
            import datetime
            timestring = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            print timestring
            2012-12-15 01:21:05
        '''



    def authenticateUserFromToken(self, token, user_id):
        '''
        Checks the user authentication by token/user_id.
        '''
        exception1 = unauthorizedRequest('Invalid authentication credentials')
        
        if token is None or user_id is None:
            raise exception1
        
        try:
            logging.info("Get user credentials and check token.")
            user = User().getUserByID(user_id)
            logging.debug("Check the token of user "+str(user_id)+".")
            if user.token==token and self.__isAnExpiredToken(user.token_timestamp)==False:
                tenantName = User().getTenantName(user.tenant_id)
                userobj = UserData(user.id, user.username, tenantName, user.mail)
                userobj.setToken(user.token, user.token_timestamp)
                logging.debug("Found user "+str(user_id)+" with a valid token.")
                return userobj
            raise Exception
        except Exception:
            logging.debug("User "+str(user_id)+" not found.")
            raise exception1



    def authenticateUserFromCredentials(self, username, password, tenant):
        '''
        Checks the user authentication by username/password/tenant.
        '''
        exception1 = unauthorizedRequest('Invalid authentication credentials')
        
        if username is None or password is None or tenant is None:
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
        if tenantName != tenant:
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



    def authenticateUserFromRESTRequest(self, request):
        '''
        Manages the authentication process via REST.
        Reads the header fields that starts with "X-Auth-" and 
        call the proper methods to check the user authentication.
        '''
        username = request.get_header("X-Auth-User")
        password = request.get_header("X-Auth-Pass")
        tenant = request.get_header("X-Auth-Tenant")
        
        token = request.get_header("X-Auth-Token")
        user_id = request.get_header("X-Auth-UserId")
        
        if token is not None and user_id is not None:
            return self.authenticateUserFromToken(token, user_id)
            
        elif username is not None and password is not None and tenant is not None:
            print("dd")
            return self.authenticateUserFromCredentials(username, password, tenant)
        
        raise wrongRequest('Wrong authentication request: send user/password/tenant or token/userid')

