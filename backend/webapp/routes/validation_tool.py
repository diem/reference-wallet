from http import HTTPStatus

import offchain
from flask import Blueprint, request
from wallet.services import validation_tool as validation_tool_service
from webapp.schemas import (
    FundsPullPreApprovalRequestCreationResponse,
    FundsPullPreApprovalRequest,
    PreparePaymentInfoResponse,
)

from .strict_schema_view import (
    StrictSchemaView,
    response_definition,
    body_parameter,
    path_string_param,
)

validation_tool = Blueprint("validation_tool", __name__)


class ValidationToolRoutes:
    class ValidationToolView(StrictSchemaView):
        tags = ["ValidationTool"]

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

    class CreateP2MPaymentAsReceiver(ValidationToolView):
        summary = "Create internal payment info record for testing purpose"
        parameters = [
            path_string_param(
                name="action",
                description="payment action",
            ),
        ]
        responses = {
            HTTPStatus.OK: response_definition(
                "Reference Id and Vasp Address", schema=PreparePaymentInfoResponse
            ),
        }

        def post(self, action: str = "charge"):
            (
                reference_id,
                my_address,
            ) = validation_tool_service.prepare_payment_as_receiver(
                self.user.account_id, action
            )

            return (
                {
                    "reference_id": reference_id,
                    "address": my_address,
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
