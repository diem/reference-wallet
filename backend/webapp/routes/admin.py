# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""Admin endpoints"""

from http import HTTPStatus

from flask import Blueprint, request
from requests import HTTPError

from diem_utils.sdks.liquidity import LpClient
from wallet.services import user as user_service
from wallet.services.transaction import get_total_balance
from wallet.types import UsernameExistsError
from webapp.schemas import (
    Users,
    UserCreationRequest,
    PendingSettlement,
    DebtSettlement,
    Error,
    TotalUsers,
    Balances,
)
from .strict_schema_view import (
    StrictSchemaView,
    query_bool_param,
    response_definition,
    url_bool_to_python,
    body_parameter,
    path_uuid_param,
)

admin = Blueprint("admin", __name__)


class AdminRoutes:
    class AdminView(StrictSchemaView):
        tags = ["admin"]
        require_admin_privileges = True

    class GetUsersView(AdminView):
        summary = "Get users"
        parameters = [
            query_bool_param(
                name="admin",
                description="If provided, filters the users by their privilege",
                required=False,
            ),
        ]
        responses = {HTTPStatus.OK: response_definition("Users", schema=Users)}

        def get(self):
            is_admin = request.args.get("admin", default=None, type=url_bool_to_python)

            if is_admin is None:
                raw_users = user_service.get_users()
            elif is_admin:
                raw_users = user_service.get_users(user_service.UsersFilter.Admins)
            else:
                raw_users = user_service.get_users(user_service.UsersFilter.NotAdmins)

            users = [
                {
                    "id": user.id,
                    "username": user.username,
                    "registration_status": user.registration_status,
                    "is_admin": user.is_admin,
                    "is_blocked": user.is_blocked,
                    "first_name": user.first_name if user.first_name else "",
                    "last_name": user.last_name if user.last_name else "",
                }
                for user in raw_users
            ]
            return {"users": users}, HTTPStatus.OK

    class CreateUserView(AdminView):
        summary = "Create a new user"
        parameters = [
            body_parameter(UserCreationRequest),
        ]
        responses = {
            HTTPStatus.OK: response_definition("User successfully created."),
            HTTPStatus.CONFLICT: response_definition(
                "Username already exists.", schema=Error
            ),
        }

        def post(self):
            user = request.json

            try:
                uid = user_service.create_new_user(
                    username=user["username"],
                    password=user["password"],
                    is_admin=user["is_admin"],
                    first_name=user["first_name"],
                    last_name=user["last_name"],
                )
            except UsernameExistsError:
                return self.respond_with_error(
                    HTTPStatus.CONFLICT, "Username already exists"
                )

            return str(uid), HTTPStatus.OK

    class BlockUserView(AdminView):
        summary = "Block existing user"
        parameters = [
            path_uuid_param("user_id", "ID of an existing user"),
        ]
        responses = {
            HTTPStatus.OK: response_definition("Blocked"),
            HTTPStatus.NOT_FOUND: response_definition("Unknown user ID"),
        }

        def put(self, user_id: int):
            try:
                user_service.block_user(user_id)
            except KeyError:
                return "Unknown user", HTTPStatus.NOT_FOUND

            return "OK", HTTPStatus.OK

    class GetSettlementView(AdminView):
        summary = "Get pending settlement details"
        responses = {
            HTTPStatus.OK: response_definition(
                "Pending settlement details", schema=PendingSettlement
            )
        }

        def get(self):
            lp_client = LpClient()
            debt_list = lp_client.get_debt()

            return (
                {
                    "debt": [
                        {
                            "debt_id": d.debt_id,
                            "currency": d.currency.value,
                            "amount": d.amount,
                        }
                        for d in debt_list
                    ]
                },
                HTTPStatus.OK,
            )

    class SettleDebtView(AdminView):
        summary = "Settle outstanding debt"
        parameters = [
            body_parameter(DebtSettlement),
            path_uuid_param("debt_id", "ID of an outstanding debt"),
        ]
        responses = {
            HTTPStatus.OK: response_definition("Settled"),
            HTTPStatus.CONFLICT: response_definition("The debt is already settled"),
            HTTPStatus.NOT_FOUND: response_definition("Unknown debt ID"),
        }

        def put(self, debt_id: str):
            settlement_confirmation = request.json["settlement_confirmation"]

            lp_client = LpClient()
            try:
                lp_client.settle(debt_id, settlement_confirmation)
            except HTTPError as e:
                return "Failed", e.response.status_code

            return "OK", HTTPStatus.OK

    class GetWalletTotalBalancesView(AdminView):
        summary = "Get total balances for the whole wallet"
        responses = {
            HTTPStatus.OK: response_definition("Wallet total balances", schema=Balances)
        }

        def get(self):
            return (
                {
                    "balances": [
                        {"currency": currency.value, "balance": int(balance),}
                        for currency, balance in get_total_balance().total.items()
                    ]
                },
                HTTPStatus.OK,
            )

    class GetWalletUserCountView(AdminView):
        summary = "Get total wallet user count"
        responses = {
            HTTPStatus.OK: response_definition(
                "Total wallet user count", schema=TotalUsers
            )
        }

        def get(self):
            return {"user_count": user_service.get_user_count()}, HTTPStatus.OK
