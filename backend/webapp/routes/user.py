# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

""" The Accounts API layer that handles user creation, information management and updates. """
from datetime import date
from http import HTTPStatus

from flask import (
    Blueprint,
    request,
    current_app,
)

from wallet.services import user as user_service, kyc
from wallet.types import (
    UserInfo,
    LoginError,
    UsernameExistsError,
)
from .strict_schema_view import StrictSchemaView, response_definition
from ..schemas import Error

user = Blueprint("user/v1", __name__, url_prefix="/")


class UserRoutes:
    class UserView(StrictSchemaView):
        tags = ["User"]

    class CreateUser(UserView):
        summary = (
            "Creates a new user account with a globally unique username and password"
        )
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Auth Token"),
            HTTPStatus.CONFLICT: response_definition(
                "User already exist", schema=Error
            ),
        }
        require_authenticated_user = False

        def post(self):
            user_params = request.json
            username = user_params["username"]
            password = user_params["password"]
            try:
                user_id = user_service.create_new_user(username, password)
            except UsernameExistsError as e:
                return self.respond_with_error(HTTPStatus.CONFLICT, str(e))

            token_id = user_service.add_token(user_id)
            return token_id, HTTPStatus.OK

    class GetUser(UserView):
        summary = "Returns user metadata information"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition(
                "User object with user metadata", schema=None
            ),
        }

        def get(self):
            user_info = UserInfo.from_obj(self.user)
            return user_info.to_dict(), HTTPStatus.OK

    class UpdateUser(UserView):
        summary = "Updates user information with the given info, such as name, address, DOB, and nationality    "
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition(
                "Updated user object with user metadata"
            ),
        }

        def put(self):
            user = self.user

            data = request.json

            if kyc.is_verified(user.id):
                #  for now we don't support changing personal info after KYC (should trigger a new KYC process)
                info = dict(
                    selected_fiat_currency=data["selected_fiat_currency"],
                    selected_language=data["selected_language"],
                )
                user_service.update_user(user.id, **info)
            else:  # if not verified - start a new KYC process
                kyc.process_user_kyc(
                    user_id=user.id,
                    selected_fiat_currency=data["selected_fiat_currency"],
                    selected_language=data["selected_language"],
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    dob=date.fromisoformat(data["dob"]) if data["dob"] else None,
                    phone=data["phone"],
                    country=data["country"],
                    state=data["state"],
                    city=data["city"],
                    address_1=data["address_1"],
                    address_2=data["address_2"],
                    zip=data["zip"],
                )

            user = user_service.get_user(user.id)
            return UserInfo.from_obj(user).to_dict(), HTTPStatus.OK

    class SignIn(UserView):
        summary = "Returns user token for client session. Pass in the returned session for all other requests"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Auth token"),
            HTTPStatus.NOT_FOUND: response_definition(
                "Username not found", schema=Error
            ),
            HTTPStatus.UNAUTHORIZED: response_definition(
                "Wrong Password", schema=Error
            ),
        }
        require_authenticated_user = False

        def post(self):
            data = request.json

            username = data["username"]
            password = data["password"]
            user = user_service.get_user(username=username)
            should_authorize = user_service.authorize(user=user, password=password)
            if should_authorize == LoginError.SUCCESS:
                token_id = user_service.add_token(user.id)
                return token_id, HTTPStatus.OK
            elif should_authorize == LoginError.USER_NOT_FOUND:
                return self.respond_with_error(
                    HTTPStatus.NOT_FOUND, "Username not found"
                )
            elif should_authorize == LoginError.WRONG_PASSWORD:
                return self.respond_with_error(
                    HTTPStatus.UNAUTHORIZED, "Wrong password"
                )
            elif should_authorize == LoginError.UNAUTHORIZED:
                return self.respond_with_error(HTTPStatus.UNAUTHORIZED, "Unauthorized")
            elif should_authorize == LoginError.ADMIN_DISABLED:
                current_app.logger.warning(
                    "Admin access is disabled and will be rejected"
                )
                current_app.logger.warning(
                    "Enable admin access in the environment configuration"
                )
                return self.respond_with_error(
                    HTTPStatus.UNAUTHORIZED, "Admin functionality is disabled"
                )

    class SignOut(UserView):
        summary = "Logs user out and invalidates session token"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Success"),
        }

        def post(self):
            user_service.revoke_token(self.token)
            return {"success": True}, HTTPStatus.OK

    class RefreshToken(UserView):
        summary = "Extends user session expiry"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Success"),
        }

        def post(self):
            try:
                user_service.extend_token_expiration(self.token)
            except KeyError:
                return "Unauthorized", HTTPStatus.UNAUTHORIZED

            return {"success": True}, HTTPStatus.OK

    class ForgotPassword(UserView):
        summary = (
            "Forgot user password generates a password reset token and sends it to user via email. "
            "For now we mock the email verification process"
        )
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Success"),
            HTTPStatus.BAD_REQUEST: response_definition(
                "Missing username", schema=Error
            ),
            HTTPStatus.UNAUTHORIZED: response_definition(
                "Username not found", schema=Error
            ),
        }
        require_authenticated_user = False

        def post(self):
            data = request.json

            if "username" not in data:
                return self.respond_with_error(
                    HTTPStatus.BAD_REQUEST, "Missing username"
                )

            username = data["username"]
            user = user_service.get_user(username=username)
            if not user:
                return self.respond_with_error(
                    HTTPStatus.UNAUTHORIZED, "Username not found"
                )

            token = user_service.create_password_reset_token(user=user)
            return token, HTTPStatus.OK

    class ResetPassword(UserView):
        summary = "Resets user password"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Success"),
            HTTPStatus.UNAUTHORIZED: response_definition(
                "Incorrect password", schema=Error
            ),
        }
        require_authenticated_user = False

        def post(self):
            data = request.json
            reset_token = data["token"]
            new_password = data["new_password"]
            _user = user_service.get_user_by_reset_token(reset_token=reset_token)
            if _user:
                user_service.update_password(_user.id, new_password)
                return {"success": True}, HTTPStatus.OK
            else:
                return self.respond_with_error(
                    HTTPStatus.UNAUTHORIZED, "Incorrect password"
                )

    class StorePaymentMethod(UserView):
        summary = "Stores new payment method"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Success", schema=None),
        }

        def post(self):
            data = request.json

            name = data["name"]
            provider = data["provider"]
            token = data["token"]

            user_service.add_payment_method(self.user.id, name, provider, token)
            return {}, HTTPStatus.OK

    class GetPaymentMethods(UserView):
        summary = "Gets user's payment methods"
        parameters = (
            []
        )  # path_string_param(name='account_name', description="account name")
        responses = {
            HTTPStatus.OK: response_definition("Payment methods", schema=None),
        }

        def get(self):
            payment_methods = [
                {
                    "id": payment_method.id,
                    "name": payment_method.name,
                    "provider": payment_method.provider,
                    "token": payment_method.token,
                }
                for payment_method in user_service.get_payment_methods(self.user.id)
            ]
            return {"payment_methods": payment_methods}, HTTPStatus.OK
