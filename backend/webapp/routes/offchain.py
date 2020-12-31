# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus

from diem.offchain import X_REQUEST_ID, X_REQUEST_SENDER_ADDRESS
from flask import Blueprint, request
from flask.views import MethodView
from wallet.services import offchain as offchain_service
from webapp.routes.strict_schema_view import (
    StrictSchemaView,
    response_definition,
    path_string_param,
)
from webapp.schemas import PaymentCommands, PaymentCommand
from webapp.schemas import FundsPullPreApproval

logger = logging.getLogger(__name__)
offchain = Blueprint("offchain", __name__)


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
        summary = "Get funds pull pre approvals"

        responses = {HTTPStatus.OK: response_definition("Funds pull pre approvals", schema=FundsPullPreApproval)}

        def get(self, cid: str):
            pass

    class ApproveFundsPullPreApproval(OffchainView):
        summary = "Approve or reject incoming funds pull pre approval"

    class EstablishFundsPullPreApproval(OffchainView):
        summary = "Establish funds pull pre approval by payer"

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
