from http import HTTPStatus

from diem.jsonrpc import AccountNotFoundError
from wallet.services.offchain import payment as payment_service
from webapp.routes.strict_schema_view import (
    StrictSchemaView,
    query_str_param,
    response_definition,
    body_parameter,
)
from webapp.schemas import Error
from flask import Blueprint, request
from webapp.schemas import CreatePayment as CreatePaymentSchema, Payment

payment = Blueprint("payment", __name__)


class PaymentRoutes:
    class PaymentView(StrictSchemaView):
        tags = ["PaymentC"]

    class GetPaymentDetails(PaymentView):
        summary = "Get Payment Details"

        parameters = [
            query_str_param(
                name="reference_id",
                description="payment reference id",
                required=True,
            ),
            query_str_param(
                name="vasp_address",
                description="payment destination address",
                required=True,
            ),
        ]

        responses = {
            HTTPStatus.OK: response_definition("Payment", schema=Payment),
            HTTPStatus.NOT_FOUND: response_definition(
                "Command not found", schema=Error
            ),
            HTTPStatus.UNPROCESSABLE_ENTITY: response_definition(
                "Command not found", schema=Error
            ),
        }

        def get(self):
            try:
                account_id = self.user.account_id
                vasp_address = request.args["vasp_address"]
                reference_id = request.args["reference_id"]

                payment_details = payment_service.get_payment_details(
                    account_id, reference_id, vasp_address
                )

                return (
                    (
                        payment_details_to_dict(payment_details),
                        HTTPStatus.OK,
                    )
                    if payment_details
                    else self.respond_with_error(
                        HTTPStatus.NOT_FOUND,
                        f"Failed finding payment details for reference id {reference_id}",
                    )
                )
            except AccountNotFoundError as e:
                return self.respond_with_error(HTTPStatus.NOT_FOUND, str(e))
            except payment_service.P2MGeneralError as e:
                return self.respond_with_error(HTTPStatus.UNPROCESSABLE_ENTITY, str(e))

    class AddPayment(PaymentView):
        summary = "Create New Payment"

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

            payment_service.add_new_payment(
                reference_id=params.get("reference_id"),
                vasp_address=params.get("vasp_address"),
                merchant_name=params.get("merchant_name"),
                action=params.get("action"),
                currency=params.get("currency"),
                amount=amount,
                expiration=expiration,
            )

            return "OK", HTTPStatus.NO_CONTENT

    class ApprovePayment(PaymentView):
        ...

    class RejectPayment(PaymentView):
        ...


def payment_details_to_dict(
    payment_details: payment_service.PaymentDetails,
):
    return {
        "vasp_address": payment_details.vasp_address,
        "reference_id": payment_details.reference_id,
        "merchant_name": payment_details.merchant_name,
        "action": payment_details.action,
        "currency": payment_details.currency,
        "amount": payment_details.amount,
        "expiration": payment_details.expiration,
    }
