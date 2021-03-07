# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import traceback
from http import HTTPStatus
from json import JSONDecodeError

from flask import Blueprint, jsonify, make_response, current_app
from werkzeug.exceptions import HTTPException

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(HTTPException)
def handle_http_exception(error):
    """Just logs the error. Any unhandled error will eventually get here."""

    real_error = getattr(error, "original_exception", error)

    current_app.logger.exception(real_error)

    response = {
        "code": error.code,
        "error": error.description,
    }
    return make_response(jsonify(response), error.code)


@errors.app_errorhandler(JSONDecodeError)
def handle_unexpected_error(error):
    status_code = HTTPStatus.BAD_REQUEST
    response = {"code": HTTPStatus.BAD_REQUEST, "error": "Could not parse json data"}

    current_app.logger.error(f"error: {error}, exec: {traceback.format_exc()}")

    return make_response(jsonify(response), status_code)
