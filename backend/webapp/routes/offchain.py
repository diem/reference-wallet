# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus

from diem import offchain as diem_offchain
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

logger = logging.getLogger(__name__)
offchain = Blueprint("offchain", __name__)


def payment_command_to_dict(command: diem_offchain.PaymentCommand):
    payment = command.payment
    sender = payment.sender
    sender_kyc_data = sender.kyc_data
    receiver = payment.receiver
    receiver_kyc_data = receiver.kyc_data
    action = payment.action
    return {
        "my_actor_address": command.my_actor_address,
        "inbound": command.inbound,
        "cid": command.cid,
        "payment": {
            "reference_id": command.reference_id(),
            "sender": {
                "address": sender.address,
                "status": {"status": sender.status.status},
                "kyc_data": {
                    "type": sender_kyc_data.type,
                    "payload_version": sender_kyc_data.payload_version,
                    "given_name": sender_kyc_data.given_name,
                    "surname": sender_kyc_data.surname,
                    "address": sender_kyc_data.address,
                    "dob": sender_kyc_data.dob,
                    "place_of_birth": sender_kyc_data.place_of_birth,
                    "national_id": sender_kyc_data.national_id,
                    "legal_entity_name": sender_kyc_data.legal_entity_name,
                },
                "metadata": sender.metadata,
                "additional_kyc_data": sender.additional_kyc_data,
            },
            "receiver": {
                "address": receiver.address,
                "status": {"status": receiver.status.status},
                "kyc_data": {
                    "type": receiver_kyc_data.type,
                    "payload_version": receiver_kyc_data.payload_version,
                    "given_name": receiver_kyc_data.given_name,
                    "surname": receiver_kyc_data.surname,
                    "address": receiver_kyc_data.address,
                    "dob": receiver_kyc_data.dob,
                    "place_of_birth": receiver_kyc_data.place_of_birth,
                    "national_id": receiver_kyc_data.national_id,
                    "legal_entity_name": receiver_kyc_data.legal_entity_name,
                },
                "metadata": receiver.metadata,
                "additional_kyc_data": receiver.additional_kyc_data,
            },
            "action": {
                "amount": action.amount,
                "currency": action.currency,
                "action": action.action,
                "timestamp": action.timestamp,
            },
            "original_payment_reference_id": payment.original_payment_reference_id,
            "recipient_signature": payment.recipient_signature,
            "description": payment.description,
        },
    }


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
            payment_command = offchain_service.get_payment_command(transaction_id)

            return (
                payment_command_to_dict(payment_command),
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

            payments = [
                payment_command_to_dict(payment) for payment in payment_commands
            ]

            return (
                {"payment_commands": payments},
                HTTPStatus.OK,
            )

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
