import json

from flask import request


class HTTPError(Exception):
    def __init__(self, message: str, payload: dict = None):
        Exception.__init__(self)
        self.message = message
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.phrase
        rv['error_description'] = self.message
        return rv

    def __str__(self):
        args = json.dumps(request.args)
        body_len = len(request.data)
        repr = "<HTTPError message:'{message}', args:'{args}', path:'{path}', body_length: '{body_len}'>".format(
            message=self.message,
            args=args,
            path=request.path,
            body_len=body_len
        )
        return repr


class BadRequest(HTTPError):
    phrase = 'bad_request'


class AuthError(HTTPError):
    phrase = 'unauthorized'


class Forbidden(HTTPError):
    phrase = 'forbidden'


class NotFound(HTTPError):
    phrase = 'not_found'


class InternalServerError(HTTPError):
    phrase = 'internal_server_error'
