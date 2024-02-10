from flask import jsonify, make_response

from api.errors import (
    AuthError,
    BadRequest,
    Forbidden,
    InternalServerError,
    NotFound
)
from utils.logger import logger


def configure_errorhandlers(app):
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        logger.critical(f"internal server error: {error}", exc_info=True)
        response = {
            'error': 'internal_server_error',
            'error_description': 'internal server error has occurred.'
        }
        return make_response(jsonify(response), 500)

    @app.errorhandler(BadRequest)
    def custom_bad_request(error):
        logger.error(f"bad_request: {error}")
        return make_response(jsonify(error.to_dict()), 400)

    @app.errorhandler(AuthError)
    def custom_unauthorized(error):
        logger.error(f"unauthorized: {error}")
        return make_response(jsonify(error.to_dict()), 401)

    @app.errorhandler(Forbidden)
    def custom_forbidden(error):
        logger.error(f"forbidden: {error}")
        return make_response(jsonify(error.to_dict()), 403)

    @app.errorhandler(NotFound)
    def custom_not_found(error):
        logger.error(f"not_found: {error}")
        return make_response(jsonify(error.to_dict()), 404)

    @app.errorhandler(InternalServerError)
    def custom_internal_server_error(error):
        logger.error(f"internal_server_error: {error}")
        return make_response(jsonify(error.to_dict()), 500)
