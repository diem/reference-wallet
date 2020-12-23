# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus

from diem.offchain import X_REQUEST_ID, X_REQUEST_SENDER_ADDRESS
from flask import Blueprint, request
from flask.views import MethodView
from wallet.services.offchain import process_inbound_command, get_payment_command
from webapp.routes.strict_schema_view import (
    StrictSchemaView,
    response_definition,
    path_string_param,
)

logger = logging.getLogger(__name__)
offchain = Blueprint("offchain", __name__)


class OffchainRoutes:
    class OffchainView(StrictSchemaView):
        tags = ["Offchain"]

    class GetPaymentCommand(OffchainView):
        summary = "Get Payment Command"

        parameters = [
            path_string_param(name="transaction_id", description="transaction id")
        ]

        responses = {HTTPStatus.OK: response_definition("Payment Command", schema=str)}

        def get(self, transaction_id: str):
            payment_command = get_payment_command(transaction_id)

            return (
                {"ref_id": transaction_id, "payment_command": payment_command},
                HTTPStatus.OK,
            )

    class OffchainV2View(MethodView):
        def dispatch_request(self, *args, **kwargs):
            x_request_id = request.headers.get(X_REQUEST_ID)
            sender_address = request.headers.get(X_REQUEST_SENDER_ADDRESS)
            request_body = request.get_data()

            logger.info(f"[{sender_address}:{x_request_id}] offchain v2 income request")

            code, response = process_inbound_command(sender_address, request_body)

            logger.info(
                f"[{sender_address}:{x_request_id}] response: {code}, {response}"
            )

            return (response, code, {X_REQUEST_ID: x_request_id})
