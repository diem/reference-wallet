from http import HTTPStatus

from diem_utils.types.currencies import DiemCurrency
from flask import Blueprint, request
from wallet.services import validation_tool as validation_tool_service
from webapp.schemas import ConsentId

from .strict_schema_view import StrictSchemaView, response_definition

validation_tool = Blueprint("validation_tool", __name__)


class ValidationToolRoutes:
    class ValidationToolView(StrictSchemaView):
        tags = ["ValidationTool"]

    class CreateConsentRequest(ValidationToolView):
        summary = "Create consent request"

        responses = {
            HTTPStatus.OK: response_definition("New consent cid", schema=ConsentId)
        }

        def post(self):
            user = self.user
            account_id = user.account_id

            consent_details = request.json

            address = consent_details["address"]
            experation_time = consent_details["experation_time"]
            description = consent_details["description"]
            max_cumulative_amount = consent_details["max_cumulative_amount"]
            currency = DiemCurrency.XUS

            if "currency" in consent_details:
                currency = consent_details["currency"]

            funds_pre_approval_id = validation_tool_service.send_consent_request(
                user_account_id=account_id,
                address=address,
                expiration_time=experation_time,
                description=description,
                max_cumulative_amount=max_cumulative_amount,
                currency=currency,
            )

            return (
                {"funds_pre_approval_id": funds_pre_approval_id},
                HTTPStatus.OK,
            )
