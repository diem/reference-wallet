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
from webapp.schemas import Consent

logger = logging.getLogger(__name__)
offchain = Blueprint("offchain", __name__)


def payment_command_to_dict(command: diem_offchain.PaymentCommand):
    payment = command.payment
    payment_dict = {
        "reference_id": command.reference_id(),
        "sender": actor_to_dict(payment.sender),
        "receiver": actor_to_dict(payment.receiver),
        "action": action_to_dict(payment.action),
    }
    if payment.original_payment_reference_id:
        payment_dict[
            "original_payment_reference_id"
        ] = payment.original_payment_reference_id
    if payment.recipient_signature:
        payment_dict["recipient_signature"] = payment.recipient_signature
    if payment.description:
        payment_dict["description"] = payment.description
    payment_command_dict = {
        "my_actor_address": command.my_actor_address,
        "inbound": command.inbound,
        "cid": command.cid,
        "payment": payment_dict,
    }
    return payment_command_dict


def action_to_dict(action):
    return {
        "amount": action.amount,
        "currency": action.currency,
        "action": action.action,
        "timestamp": action.timestamp,
    }


def actor_to_dict(actor):
    actor_dict = {
        "address": actor.address,
        "status": {"status": actor.status.status},
    }
    if actor.metadata:
        actor_dict["metadata"] = actor.metadata
    if actor.additional_kyc_data:
        actor_dict["additional_kyc_data"] = actor.additional_kyc_data
    kyc_data = actor.kyc_data
    if kyc_data:
        actor_dict["kyc_data"] = {
            "type": kyc_data.type,
            "payload_version": kyc_data.payload_version,
            "given_name": kyc_data.given_name,
            "surname": kyc_data.surname,
            "address": kyc_data.address,
            "dob": kyc_data.dob,
            "place_of_birth": kyc_data.place_of_birth,
            "national_id": kyc_data.national_id,
            "legal_entity_name": kyc_data.legal_entity_name,
        }
    return actor_dict


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

    class GetConsents(OffchainView):
        summary = "Get consent"

        responses = {HTTPStatus.OK: response_definition("Consents", schema=Consent)}

        def get(self, cid: str):
            pass

    class ApproveConsent(OffchainView):
        summary = "Approve or reject incoming consent"

    class EstablishConsent(OffchainView):
        summary = "Establish consent by payer"

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
