from http import HTTPStatus

from diem_utils.types.currencies import DiemCurrency
from flask import Blueprint, request
from wallet.services import validation_tool as validation_tool_service
from webapp.schemas import FundsPullPreApprovalId

from .strict_schema_view import StrictSchemaView, response_definition

validation_tool = Blueprint("validation_tool", __name__)


class ValidationToolRoutes:
    class ValidationToolView(StrictSchemaView):
        tags = ["ValidationTool"]

    class CreateFundsPullPreApprovalRequest(ValidationToolView):
        summary = "Create funds_pull_pre_approval request"

        responses = {
            HTTPStatus.OK: response_definition(
                "New funds_pull_pre_approval cid", schema=FundsPullPreApprovalId
            )
        }

        def post(self):
            user = self.user
            account_id = user.account_id

            request_details = request.json

            address = request_details["address"]
            experation_time = request_details["experation_time"]
            description = request_details["description"]
            max_cumulative_amount = request_details["max_cumulative_amount"]
            currency = DiemCurrency.XUS
            cumulative_amount_unit = request_details["cumulative_amount_unit"]
            cumulative_amount_unit_value = request_details[
                "cumulative_amount_unit_value"
            ]

            if "currency" in request_details:
                currency = request_details["currency"]

            funds_pre_approval_id = (
                validation_tool_service.create_funds_pull_pre_approval_request(
                    user_account_id=account_id,
                    address=address,
                    expiration_time=experation_time,
                    description=description,
                    max_cumulative_amount=max_cumulative_amount,
                    currency=currency,
                    cumulative_amount_unit=cumulative_amount_unit,
                    cumulative_amount_unit_value=cumulative_amount_unit_value,
                )
            )

            return (
                {"funds_pre_approval_id": funds_pre_approval_id},
                HTTPStatus.OK,
            )
