from http import HTTPStatus

from diem import offchain
from diem_utils.types.currencies import DiemCurrency
from flask import Blueprint, request
from wallet.services import validation_tool as validation_tool_service
from webapp.schemas import FundsPullPreApprovalId, FundsPullPreApprovalRequest

from .strict_schema_view import StrictSchemaView, response_definition, body_parameter

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
                "ID of the new funds_pull_pre_approval object",
                schema=FundsPullPreApprovalId,
            )
        }

        def post(self):
            user = self.user
            request_details = request.json

            payer_address = request_details["payer_address"]
            description = request_details.get("description")
            should_send = request_details.get("should_send")

            max_cumulative_amount = (
                offchain.ScopedCumulativeAmountObject(
                    unit=request_details["scope"]["max_cumulative_amount"]["unit"],
                    value=request_details["scope"]["max_cumulative_amount"]["value"],
                    max_amount=offchain.CurrencyObject(
                        **request_details["scope"]["max_cumulative_amount"][
                            "max_amount"
                        ]
                    ),
                )
                if "max_cumulative_amount" in request_details["scope"]
                else None
            )

            max_transaction_amount = (
                offchain.CurrencyObject(
                    **request_details["scope"]["max_transaction_amount"]
                )
                if "max_transaction_amount" in request_details["scope"]
                else None
            )

            scope = offchain.FundPullPreApprovalScopeObject(
                type=request_details["scope"]["type"],
                expiration_timestamp=request_details["scope"]["expiration_timestamp"],
                max_cumulative_amount=max_cumulative_amount,
                max_transaction_amount=max_transaction_amount,
            )

            funds_pull_pre_approval_id = (
                validation_tool_service.request_funds_pull_pre_approval_from_another(
                    account_id=user.account_id,
                    payer_address=payer_address,
                    scope=scope,
                    description=description,
                    should_send=should_send is None or should_send,
                )
            )

            return (
                {"funds_pull_pre_approval_id": funds_pull_pre_approval_id},
                HTTPStatus.OK,
            )
