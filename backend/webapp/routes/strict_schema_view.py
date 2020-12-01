# pyre-ignore-all-errors
from http import HTTPStatus
from typing import Tuple, List, Optional

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from flasgger import SwaggerView, utils
from flask import request

from wallet.services import user

BEARER_LEN = len("Bearer ")

orig_utils_validate = utils.validate


def patched_validate(*args, **kwargs):
    kwargs["require_data"] = False
    orig_utils_validate(*args, **kwargs)


utils.validate = patched_validate


class StrictSchemaView(SwaggerView):
    """
    A Flask view handling Swagger generation and response/request schema
    validation.

    Note that, as opposed to the original Flask MethodView, the view methods
    (get, post etc.) support returning only (response, status_code) tuples.
    For errors it is possible to raise exceptions.
    """

    # Set to true if the requesting user must have admin privileges
    require_admin_privileges = False
    require_authenticated_user = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None
        self._token = None

        if self.parameters:
            for p in self.parameters:
                param_type = p.get("in", None)
                if param_type == "body":
                    self.validation = True
                    break

    @property
    def user(self):
        if self._user is None:
            raise AttributeError("User ID is unavailable when not in a request context")
        return self._user

    @property
    def token(self):
        if self._token is None:
            raise AttributeError(
                "Auth token is unavailable when not in a request context"
            )
        return self._token

    def dispatch_request(self, *args, **kwargs):
        if self.require_authenticated_user:
            token = get_auth_token_from_headers(request.headers)
            if not user.is_valid_token(token):
                return self.respond_with_error(
                    HTTPStatus.UNAUTHORIZED, "Unauthenticated"
                )

            self._token = token
            the_user = user.get_user_by_token(token)
            self._user = the_user

        if self.require_admin_privileges and not the_user.is_admin:
            return self.respond_with_error(HTTPStatus.FORBIDDEN, "Forbidden")

        response, status_code = super().dispatch_request(*args, **kwargs)
        self._user = None

        validate_response(response, status_code, self.responses)

        return response, status_code

    @staticmethod
    def respond_with_error(code: int, error: str) -> Tuple[dict, int]:
        return {"error": error, "code": code}, code


def validate_response(response, http_status_code, response_definitions):
    schema_factory = (
        response_definitions.get(http_status_code, {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )
    if not schema_factory:
        return
    schema = schema_factory()
    response = schema.dump(response)
    errors = schema.validate(response)
    if errors:
        raise ResponseSchemaError(schema.__class__.__name__, response, errors)


def get_auth_token_from_headers(headers):
    return headers.get("Authorization", "")[BEARER_LEN:]


def response_definition(description, schema=None):
    """Helps to create response definitions"""
    return {
        "description": description,
        "content": {"application/json": {"schema": schema}},
    }


def body_parameter(schema):
    return {"name": "body", "in": "body", "required": True, "schema": schema}


def query_bool_param(name, description, required):
    return {
        "name": name,
        "in": "query",
        "required": required,
        "description": description,
        "schema": {"type": "boolean"},
    }


def query_int_param(name, description, required):
    return {
        "name": name,
        "in": "query",
        "required": required,
        "description": description,
        "schema": {"type": "integer"},
    }


def query_str_param(
    name, description, required, allowed_vlaues: Optional[List[str]] = None
):
    param_definition = {
        "name": name,
        "in": "query",
        "required": required,
        "description": description,
        "schema": {"type": "string"},
    }

    if allowed_vlaues:
        param_definition["enum"] = allowed_vlaues

    return param_definition


def path_uuid_param(name, description):
    return {
        "name": name,
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": "string", "format": "uuid",},
    }


def path_string_param(name, description):
    return {
        "name": name,
        "in": "path",
        "required": True,
        "description": description,
        "schema": {"type": "string"},
    }


def url_bool_to_python(value):
    if value is None:
        return None

    if value in ["True", "true", "Yes", "yes", "1"]:
        return True

    if value in ["False", "false", "No", "no", "0"]:
        return False

    raise ValueError(f"Cannot convert {value} to bool")


class ResponseSchemaError(Exception):
    def __init__(self, schema, response, errors):
        super().__init__(
            f"Response schema validation error "
            f"schema={schema}, response={response}, errors={errors}"
        )
        self.schema = schema
        self.response = response
        self.errors = errors

    def to_dict(self):
        return {
            "message": "Response schema validation error",
            "schema": self.schema,
            "response": self.response,
            "errors": self.errors,
        }
