# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import json
from functools import wraps
from http import HTTPStatus

from flask import g, request, Response

from .services.user import is_valid_token, revoke_token, get_user_by_token


def current_user():
    if hasattr(g, "current_user"):
        return g.current_user


def get_token_id_from_request() -> str:
    return request.headers["Authorization"].split()[1]


def verify_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_id = get_token_id_from_request()

        if is_valid_token(token_id):
            g.current_user = get_user_by_token(token_id)
            return f(*args, **kwargs)
        else:
            revoke_token(token_id)
            error = json.dumps(
                {
                    "code": HTTPStatus.UNAUTHORIZED,
                    "error": "Invalid authorization token",
                }
            )
            return Response(
                error, status=HTTPStatus.UNAUTHORIZED, mimetype="application/json"
            )

    return decorated_function
