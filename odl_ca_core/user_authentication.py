'''
Created on 18 set 2015

@author: Andrea
'''

from odl_ca_core.sql.user import User
from odl_ca_core.exception import unauthorizedRequest


class UserData(object):
    
    def __init__(self, username=None, password=None, tenant=None):
        self.username = username
        self.password = password
        self.tenant = tenant
        
        # User ID cache
        self._userID = None
    
    def getUserID(self):
        if self._userID is not None:
            return self._userID
        return User().getUser(self.username).id
    
    def getUserData(self, user_id):
        user = User().getUserFromID(user_id)
        self.username = user.name
        self.password =user.password
        tenant = User().getTenantName(user.tenant_id)
        self.tenant = tenant

class UserAuthentication(object):
    

    def authenticateUserFromRESTRequest(self, request):
        
        username = request.get_header("X-Auth-User")
        password = request.get_header("X-Auth-Pass")
        tenant = request.get_header("X-Auth-Tenant")  
        
        return self.authenticateUserFromCredentials(username, password, tenant)
    
    
    
    def authenticateUserFromCredentials(self, username, password, tenant):
        if username is None or password is None or tenant is None:
                raise unauthorizedRequest('Authentication credentials required')
        
        user = User().getUser(username)
        if user.password == password:
            tenantName = User().getTenantName(user.tenant_id)
            if tenantName == tenant:
                userobj = UserData(username, password, tenant)
                return userobj
        raise unauthorizedRequest('Invalid authentication credentials')