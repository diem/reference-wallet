# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus

from diem.offchain import (
    X_REQUEST_ID,
    X_REQUEST_SENDER_ADDRESS,
    FundPullPreApprovalStatus,
)
from flask import Blueprint, request
from flask.views import MethodView
from wallet.services import fund_pull_pre_approval as fppa_service
from wallet.services import offchain as offchain_service
from webapp.routes.strict_schema_view import (
    StrictSchemaView,
    response_definition,
    path_string_param,
    body_parameter,
    query_str_param,
)
from webapp.schemas import (
    PaymentCommands,
    PaymentCommand,
    FundsPullPreApprovalList,
    UpdateFundsPullPreApproval,
    Error,
    CreateAndApproveFundPullPreApproval,
)

logger = logging.getLogger(__name__)
offchain = Blueprint("offchain", __name__)


def preapproval_command_to_dict(preapproval: fppa_service.FPPAObject):
    preapproval_object = preapproval.funds_pull_pre_approval
    scope = preapproval_object.scope

    result = {
        "address": preapproval_object.address,
        "biller_address": preapproval_object.biller_address,
        "funds_pull_pre_approval_id": preapproval_object.funds_pull_pre_approval_id,
        "status": preapproval_object.status,
        "scope": {
            "type": scope.type,
            "expiration_timestamp": scope.expiration_timestamp,
        },
        "biller_name": preapproval.biller_name,
        "created_at": preapproval.created_timestamp,
        "updated_at": preapproval.updated_at,
        "approved_at": preapproval.approved_at,
    }

    if preapproval_object.description is not None:
        result["description"] = preapproval_object.description

    if scope.max_cumulative_amount is not None:
        max_cumulative_amount = scope.max_cumulative_amount
        result["scope"]["max_cumulative_amount"] = {
            "unit": max_cumulative_amount.unit,
            "value": max_cumulative_amount.value,
            "max_amount": {
                "amount": max_cumulative_amount.max_amount.amount,
                "currency": max_cumulative_amount.max_amount.currency,
            },
        }

    if scope.max_transaction_amount is not None:
        max_transaction_amount = scope.max_transaction_amount
        result["scope"]["max_transaction_amount"] = {
            "amount": max_transaction_amount.amount,
            "currency": max_transaction_amount.currency,
        }

    return result


class OffchainRoutes:
    class OffchainView(StrictSchemaView):
        tags = ["Offchain"]

    class GetPaymentCommand(OffchainView):
        summary = "Get Payment Command"

        parameters = [
            path_string_param(
                name="transaction_id", description="transaction internal id"
            )
        ]

        responses = {
            HTTPStatus.OK: response_definition("Payment Command", schema=PaymentCommand)
        }

        def get(self, transaction_id: int):
            payment_command = offchain_service.get_payment_command_json(transaction_id)

            return (
                {"payment_command": payment_command},
                HTTPStatus.OK,
            )

    class GetAccountPaymentCommands(OffchainView):
        summary = "Get Account Payment Commands"

        responses = {
            HTTPStatus.OK: response_definition(
                "Account Payment Commands", schema=PaymentCommands
            )
        }

        def get(self):
            payment_commands = offchain_service.get_account_payment_commands(
                self.user.account_id
            )

            return (
                {"payment_commands": payment_commands},
                HTTPStatus.OK,
            )

    class GetFundsPullPreApprovals(OffchainView):
        summary = "Get funds pull pre approvals of a user"

        parameters = [
            query_str_param(
                name="status",
                description="approval status in DB",
                required=False,
                allowed_vlaues=["pending", "rejected", "valid", "closed"],
            ),
        ]

        responses = {
            HTTPStatus.OK: response_definition(
                "Funds pull pre approvals", schema=FundsPullPreApprovalList
            )
        }

        def get(self):
            status = request.args["status"] if "status" in request.args else None

            if status is None:
                approvals = fppa_service.get_funds_pull_pre_approvals(
                    self.user.account_id
                )
            else:
                approvals = fppa_service.get_funds_pull_pre_approvals_by_status(
                    self.user.account_id, status
                )

            serialized_preapprovals = [
                preapproval_command_to_dict(approval) for approval in approvals
            ]

            return (
                {"funds_pull_pre_approvals": serialized_preapprovals},
                HTTPStatus.OK,
            )

    class UpdateFundPullPreApprovalStatus(OffchainView):
        summary = "update funds pull pre approval status"
        parameters = [
            body_parameter(UpdateFundsPullPreApproval),
            path_string_param(
                name="funds_pull_pre_approval_id",
                description="funds pull pre approval id",
            ),
        ]

        responses = {
            HTTPStatus.NO_CONTENT: response_definition("Request accepted"),
            HTTPStatus.NOT_FOUND: response_definition(
                "Command not found", schema=Error
            ),
        }

        def put(self, funds_pull_pre_approval_id: str):
            params = request.json

            status: str = params["status"]

            try:
                if status == FundPullPreApprovalStatus.valid:
                    fppa_service.approve(funds_pull_pre_approval_id)
                elif status == FundPullPreApprovalStatus.rejected:
                    fppa_service.reject(funds_pull_pre_approval_id)
                elif status == FundPullPreApprovalStatus.closed:
                    fppa_service.close(funds_pull_pre_approval_id)
                else:
                    return self.respond_with_error(
                        HTTPStatus.BAD_REQUEST,
                        f"Updating status to {status} is not supported",
                    )
            except fppa_service.FundsPullPreApprovalCommandNotFound:
                return self.respond_with_error(
                    HTTPStatus.NOT_FOUND,
                    f"Funds pre-approval ID {funds_pull_pre_approval_id} not found",
                )

            return "OK", HTTPStatus.NO_CONTENT

    class CreateAndApprove(OffchainView):
        summary = "Create and approve fund pull pre approval by payer"
        parameters = [
            body_parameter(CreateAndApproveFundPullPreApproval),
        ]
        responses = {
            HTTPStatus.OK: response_definition(
                "Funds pull pre approvals request successfully sent"
            ),
        }

        def post(self):
            params = request.json

            account_id: int = self.user.account_id
            biller_address: str = params["biller_address"]
            funds_pull_pre_approval_id: str = params["funds_pull_pre_approval_id"]
            scope: dict = params["scope"]
            funds_pull_pre_approval_type: str = scope["type"]
            expiration_timestamp: int = scope["expiration_timestamp"]

            max_cumulative_amount = {}
            if scope.get("max_cumulative_amount") is not None:
                max_cumulative_amount_object = scope.get("max_cumulative_amount")
                max_cumulative_amount = dict(
                    max_cumulative_unit=max_cumulative_amount_object.get("unit"),
                    max_cumulative_unit_value=max_cumulative_amount_object.get("value"),
                    max_cumulative_amount=max_cumulative_amount_object.get(
                        "max_amount"
                    ).get("amount"),
                    max_cumulative_amount_currency=max_cumulative_amount_object.get(
                        "max_amount"
                    ).get("currency"),
                )

            max_transaction_amount = {}
            if scope.get("max_transaction_amount") is not None:
                max_transaction_amount_object = scope.get("max_transaction_amount")
                max_transaction_amount = dict(
                    max_transaction_amount=max_transaction_amount_object.get("amount"),
                    max_transaction_amount_currency=max_transaction_amount_object.get(
                        "currency"
                    ),
                )

            description: str = params.get("description")

            fppa_service.create_and_approve(
                account_id=account_id,
                biller_address=biller_address,
                funds_pull_pre_approval_id=funds_pull_pre_approval_id,
                funds_pull_pre_approval_type=funds_pull_pre_approval_type,
                expiration_timestamp=expiration_timestamp,
                description=description,
                **max_cumulative_amount,
                **max_transaction_amount,
            )

            return "OK", HTTPStatus.OK

    class OffchainV2View(MethodView):
        def dispatch_request(self, *args, **kwargs):
            x_request_id = request.headers.get(X_REQUEST_ID)
            sender_address = request.headers.get(X_REQUEST_SENDER_ADDRESS)
            request_body = request.get_data()

            logger.info(f"[{sender_address}:{x_request_id}] offchain v2 income request")

            code, response = offchain_service.process_inbound_command(
                sender_address, request_body
            )

            logger.info(
                f"[{sender_address}:{x_request_id}] response: {code}, {response}"
            )

            return (response, code, {X_REQUEST_ID: x_request_id})
