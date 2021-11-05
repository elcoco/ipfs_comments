#!/usr/bin/env python3
import logging
import datetime

logger = logging.getLogger('app')

class APIException(Exception): pass

class AuthException(APIException): pass
class AuthUserNotFoundError(AuthException):pass
class AuthUserNotAddedError(AuthException):pass
class AuthUserNotChangedError(AuthException):pass

class ConfigException(APIException): pass
class ConfigCreateDirectoryError(ConfigException): pass
class ConfigKeyError(ConfigException): pass
class ConfigParseError(ConfigException): pass
class ConfigFileNotFoundError(ConfigException): pass

class ClientAPIError(Exception): pass
class ClientAPITokenFileNotFoundError(ClientAPIError): pass

class APIResponseBaseException(Exception):
    def to_dict(self):
        msg = {}
        msg["error"] = {}
        msg["error"]["status_code"] = self.status_code
        msg["error"]["message"] = self.message
        msg["error"]["payload"] = self.payload
        msg["error"]["trace"] = self.trace
        msg["error"]["status"] = self.status
        msg["error"]["time"] = datetime.datetime.utcnow()
        return msg

class UnauthorizedError(APIResponseBaseException):
    def __init__(self, message="Unauthorized", payload={}, trace=None):
        self.status_code = 401
        self.payload = payload
        self.trace = str(trace)
        self.status = "401: Unauthorized"
        self.message = message

class ForbiddenError(APIResponseBaseException):
    def __init__(self, message="Forbidden", payload={}, trace=None):
        self.status_code = 403
        self.payload = payload
        self.trace = str(trace)
        self.status = "403: Forbidden"
        self.message = message

class NotFoundError(APIResponseBaseException):
    def __init__(self, message="Not found", payload={}, trace=None):
        self.status_code = 404
        self.payload = payload
        self.trace = str(trace)
        self.status = "404: Not found"
        self.message = message

class BadRequestError(APIResponseBaseException):
    """ For mallformed requests, eg: missing required attributes """
    def __init__(self, message="Bad request", payload={}, trace=None):
        self.status_code = 400
        self.payload = payload
        self.trace = str(trace)
        self.status = "400: Bad request"
        self.message = message

class ConflictError(APIResponseBaseException):
    """ For unique errors in database """
    def __init__(self, message="Conflict", payload={}, trace=None):
        self.status_code = 409
        self.payload = payload
        self.trace = str(trace)
        self.status = "409: Conflict"
        self.message = message

class InternalServerError(APIResponseBaseException):
    def __init__(self, message="Internal server error", payload={}, trace=None):
        self.status_code = 500
        self.payload = payload
        self.trace = str(trace)
        self.status = "500: Internal Server Error"
        self.message = message
