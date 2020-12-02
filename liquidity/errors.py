# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import traceback
from http import HTTPStatus
from json import JSONDecodeError

from flask import Blueprint, jsonify, current_app

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(Exception)
def handle_unexpected_error(error):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    response = {
        "code": HTTPStatus.INTERNAL_SERVER_ERROR,
        "error": "An unexpected error has occurred.",
    }

    current_app.logger.error(f"error: {error}, exec: {traceback.format_exc()}")

    return jsonify(response), status_code


@errors.app_errorhandler(JSONDecodeError)
def handle_unexpected_error(error):
    status_code = HTTPStatus.BAD_REQUEST
    response = {"code": HTTPStatus.BAD_REQUEST, "error": "Could not parse json data"}

    return jsonify(response), status_code
