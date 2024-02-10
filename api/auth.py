from functools import wraps

import flask

from api.errors import AuthError
from config import AppConfig
from utils.logger import logger


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        slack_verify_token = flask.request.form.get('token', '')
        if not slack_verify_token == AppConfig.slack_verify_token:
            raise AuthError("authorization malformed!")

        return f(*args, **kwargs)

    return decorated
