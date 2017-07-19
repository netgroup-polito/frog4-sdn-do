class NffgUselessInformations(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(NffgUselessInformations, self).__init__(message)
        
    def get_mess(self):
        return self.message


class UserTokenExpired(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(UserTokenExpired, self).__init__(message)
        
    def get_mess(self):
        return self.message


class UserNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(UserNotFound, self).__init__(message)
        
    def get_mess(self):
        return self.message


class TenantNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(TenantNotFound, self).__init__(message)
        
    def get_mess(self):
        return self.message


class WrongConfigurationFile(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(WrongConfigurationFile, self).__init__(message)
        
    def get_mess(self):
        return self.message


class sessionNotFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(sessionNotFound, self).__init__(message)
        
    def get_mess(self):
        return self.message


class wrongRequest(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(wrongRequest, self).__init__(message)
    
    def get_mess(self):
        return self.message


class unauthorizedRequest(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(unauthorizedRequest, self).__init__(message)
    
    def get_mess(self):
        return self.message


class NoPathBetweenSwitches(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(NoPathBetweenSwitches, self).__init__(message)
    
    def get_mess(self):
        return self.message


class NF_FGValidationError(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(NF_FGValidationError, self).__init__(message)
    
    def get_mess(self):
        return self.message


class WrongNumberOfPorts(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(WrongNumberOfPorts, self).__init__(message)
    
    def get_mess(self):
        return self.message


class GraphError(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(GraphError, self).__init__(message)
    
    def get_mess(self):
        return self.message


class MessagingError(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(MessagingError, self).__init__(message)

    def get_mess(self):
        return self.message


class NoGraphFound(Exception):
    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(NoGraphFound, self).__init__(message)