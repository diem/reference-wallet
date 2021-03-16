from http import HTTPStatus

from diem import offchain
from flask import Blueprint, request
from wallet.services import validation_tool as validation_tool_service
from wallet.services.validation_tool import add_payment_command_as_receiver
from webapp.schemas import (
    FundsPullPreApprovalRequestCreationResponse,
    FundsPullPreApprovalRequest,
)

from .strict_schema_view import StrictSchemaView, response_definition, body_parameter
from webapp.schemas import CreatePaymentAsReceiverCommand as CreatePaymentCommandSchema


validation_tool = Blueprint("validation_tool", __name__)


class ValidationToolRoutes:
    class ValidationToolView(StrictSchemaView):
        tags = ["ValidationTool"]

    class AddPaymentCommandAsReceiver(ValidationToolView):
        summary = "save payment command as receiver"

        parameters = [body_parameter(CreatePaymentCommandSchema)]

        responses = {
            HTTPStatus.NO_CONTENT: response_definition(
                "Request accepted. You should poll for status updates."
            )
        }

        def post(self):
            params = request.json

            add_payment_command_as_receiver(
                account_id=self.user.account_id,
                reference_id=params["reference_id"],
                sender_address=params["sender_address"],
                amount=params["amount"],
                currency=params["currency"],
                action=params["action"],
                expiration=params["expiration"],
            )

            return "OK", HTTPStatus.NO_CONTENT

    class CreateFundsPullPreApprovalRequest(ValidationToolView):
        summary = "Send funds pull pre-approval request to another VASP"
        parameters = [
            body_parameter(FundsPullPreApprovalRequest),
        ]
        responses = {
            HTTPStatus.OK: response_definition(
                "ID of the new funds_pull_pre_approval object and the address who been generate for the created request",
                schema=FundsPullPreApprovalRequestCreationResponse,
            )
        }

        def post(self):
            user = self.user
            request_details = request.json

            payer_address = request_details.get("payer_address")
            description = request_details.get("description")

            scope = get_scope_from_request_details(request_details)

            if payer_address:
                (
                    funds_pull_pre_approval_id,
                    address,
                ) = validation_tool_service.request_funds_pull_pre_approval_from_another(
                    account_id=user.account_id,
                    payer_address=payer_address,
                    scope=scope,
                    description=description,
                )
            else:
                (
                    funds_pull_pre_approval_id,
                    address,
                ) = validation_tool_service.create_preapproval_for_unknown_payer(
                    account_id=user.account_id,
                    scope=scope,
                    description=description,
                )

            return (
                {
                    "funds_pull_pre_approval_id": funds_pull_pre_approval_id,
                    "address": address,
                },
                HTTPStatus.OK,
            )


def get_scope_from_request_details(request_details):
    max_cumulative_amount = (
        offchain.ScopedCumulativeAmountObject(
            unit=request_details["scope"]["max_cumulative_amount"]["unit"],
            value=request_details["scope"]["max_cumulative_amount"]["value"],
            max_amount=offchain.CurrencyObject(
                **request_details["scope"]["max_cumulative_amount"]["max_amount"]
            ),
        )
        if "max_cumulative_amount" in request_details["scope"]
        else None
    )
    max_transaction_amount = (
        offchain.CurrencyObject(**request_details["scope"]["max_transaction_amount"])
        if "max_transaction_amount" in request_details["scope"]
        else None
    )

    return offchain.FundPullPreApprovalScopeObject(
        type=request_details["scope"]["type"],
        expiration_timestamp=request_details["scope"]["expiration_timestamp"],
        max_cumulative_amount=max_cumulative_amount,
        max_transaction_amount=max_transaction_amount,
    )
