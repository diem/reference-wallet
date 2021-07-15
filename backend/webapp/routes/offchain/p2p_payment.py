from http import HTTPStatus

import offchain as diem_offchain
from offchain import Status
from wallet.services.offchain import p2p_payment as pc_service
from webapp.routes.strict_schema_view import (
    StrictSchemaView,
    path_string_param,
    response_definition,
    body_parameter,
)
from webapp.schemas import PaymentCommand, PaymentCommands, Error
from flask import Blueprint, request
from webapp.schemas import CreatePayment as CreatePaymentSchema

p2p_payments = Blueprint("payment_command", __name__)


class P2PPaymentRoutes:
    class PaymentCommandView(StrictSchemaView):
        tags = ["PaymentCommand"]

    class GetP2PPayment(PaymentCommandView):
        summary = "Get Payment Command"

        parameters = [
            path_string_param(name="reference_id", description="command reference id")
        ]

        responses = {
            HTTPStatus.OK: response_definition("Payment Command", schema=PaymentCommand)
        }

        def get(self, reference_id: int):
            payment_command = pc_service.get_payment_command(reference_id)

            return (
                payment_command_to_dict(payment_command),
                HTTPStatus.OK,
            )

    class GetAccountP2PPayments(PaymentCommandView):
        summary = "Get Account Payment Commands"

        responses = {
            HTTPStatus.OK: response_definition(
                "Account Payment Commands", schema=PaymentCommands
            )
        }

        def get(self):
            payment_commands = pc_service.get_account_payment_commands(
                self.user.account_id
            )

            payments = [
                payment_command_to_dict(payment) for payment in payment_commands
            ]

            return (
                {"payment_commands": payments},
                HTTPStatus.OK,
            )

    class CreateP2PPaymentAsSender(PaymentCommandView):
        summary = "Create New Payment Command"

        parameters = [body_parameter(CreatePaymentSchema)]

        responses = {
            HTTPStatus.NO_CONTENT: response_definition(
                "Request accepted. You should poll for status updates."
            )
        }

        def post(self):
            params = request.json

            amount = int(params.get("amount")) if params.get("amount") else None
            expiration = (
                int(params.get("expiration")) if params.get("expiration") else None
            )

            pc_service.add_payment_command_as_sender(
                account_id=self.user.account_id,
                reference_id=params.get("reference_id"),
                vasp_address=params.get("vasp_address"),
                merchant_name=params.get("merchant_name"),
                action=params.get("action"),
                currency=params.get("currency"),
                amount=amount,
                expiration=expiration,
            )

            return "OK", HTTPStatus.NO_CONTENT

    class ApproveP2PPayment(PaymentCommandView):
        summary = "Approve Payment Command"

        parameters = [
            path_string_param(
                name="reference_id",
                description="command reference id",
            ),
        ]

        responses = {
            HTTPStatus.NO_CONTENT: response_definition("Request accepted"),
            HTTPStatus.NOT_FOUND: response_definition(
                "Command not found", schema=Error
            ),
        }

        def post(self, reference_id: str):
            pc_service.update_payment_command_sender_status(
                reference_id, Status.needs_kyc_data
            )

            return "OK", HTTPStatus.NO_CONTENT

    class RejectP2PPayment(PaymentCommandView):
        summary = "Reject Payment Command"

        parameters = [
            path_string_param(
                name="reference_id",
                description="command reference id",
            ),
        ]

        responses = {
            HTTPStatus.NO_CONTENT: response_definition("Request accepted"),
            HTTPStatus.NOT_FOUND: response_definition(
                "Command not found", schema=Error
            ),
        }

        def post(self, reference_id: str):
            pc_service.update_payment_command_sender_status(reference_id, Status.abort)

            return "OK", HTTPStatus.NO_CONTENT


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
