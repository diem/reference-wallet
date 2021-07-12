import json
import uuid

import pytest
import offchain
from flask import Response
from flask.testing import Client
from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import TIMESTAMP
from tests.webapp_tests.routes.test_fund_pull_pre_approval import ADDRESS
from wallet.services import validation_tool as validation_tool_service

FUNDS_PULL_PRE_APPROVAL_ID = str(uuid.uuid4())
CURRENCY = "XUS"
ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
REFERENCE_ID = "2632a018-e492-4487-81f3-775d6ecfb6ef"


@pytest.fixture
def mock_validation_tool_service(monkeypatch):
    def factory(method_name: str, will_return=None):
        calls = []

        def mock(**argv):
            calls.append(argv)
            return will_return

        monkeypatch.setattr(validation_tool_service, method_name, mock)
        return calls

    return factory


class TestRequestFundsPullPreApprovalFromAnother:
    def test_all_request_fields(
        self, authorized_client: Client, mock_validation_tool_service
    ):
        """
        Sends the request with all the fields specified.
        """

        expected_max_cumulative_amount = {
            "unit": "week",
            "value": 1,
            "max_amount": {
                "amount": 100,
                "currency": CURRENCY,
            },
        }
        expected_max_transaction_amount = {
            "amount": 10,
            "currency": CURRENCY,
        }
        expected_scope = {
            "type": "consent",
            "expiration_timestamp": TIMESTAMP,
            "max_cumulative_amount": expected_max_cumulative_amount,
            "max_transaction_amount": expected_max_transaction_amount,
        }
        request_body = {
            "payer_address": "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc",
            "description": "Test create funds_pull_pre_approval request",
            "scope": expected_scope,
        }

        calls = mock_validation_tool_service(
            "request_funds_pull_pre_approval_from_another",
            will_return=(FUNDS_PULL_PRE_APPROVAL_ID, ADDRESS),
        )

        rv: Response = authorized_client.post(
            "/validation/funds_pull_pre_approvals",
            json=request_body,
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        funds_pull_pre_approval_id = rv.get_json()["funds_pull_pre_approval_id"]
        assert funds_pull_pre_approval_id == FUNDS_PULL_PRE_APPROVAL_ID

        assert len(calls) == 1
        call = calls[0]

        assert call["account_id"] == 1
        assert call["payer_address"] == request_body["payer_address"]
        assert call["description"] == request_body["description"]

        scope: offchain.FundPullPreApprovalScopeObject = call["scope"]
        assert scope.type == expected_scope["type"]
        assert scope.expiration_timestamp == expected_scope["expiration_timestamp"]

        assert scope.max_cumulative_amount is not None
        assert (
            scope.max_cumulative_amount.unit == expected_max_cumulative_amount["unit"]
        )
        assert (
            scope.max_cumulative_amount.value == expected_max_cumulative_amount["value"]
        )
        assert (
            scope.max_cumulative_amount.max_amount.amount
            == expected_max_cumulative_amount["max_amount"]["amount"]
        )
        assert (
            scope.max_cumulative_amount.max_amount.currency
            == expected_max_cumulative_amount["max_amount"]["currency"]
        )

        assert scope.max_transaction_amount is not None
        assert (
            scope.max_transaction_amount.amount
            == expected_max_transaction_amount["amount"]
        )
        assert (
            scope.max_transaction_amount.currency
            == expected_max_transaction_amount["currency"]
        )

    def test_request_nonoptional_fields_only(
        self, authorized_client: Client, mock_validation_tool_service
    ):
        """
        Sends the request with only the non-optional fields specified.
        """

        expected_scope = {
            "type": "consent",
            "expiration_timestamp": TIMESTAMP,
        }
        request_body = {
            "payer_address": "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc",
            "scope": expected_scope,
        }

        calls = mock_validation_tool_service(
            "request_funds_pull_pre_approval_from_another",
            will_return=(FUNDS_PULL_PRE_APPROVAL_ID, ADDRESS),
        )

        rv: Response = authorized_client.post(
            "/validation/funds_pull_pre_approvals",
            json=request_body,
        )

        assert rv.status_code == 200, rv.get_data()
        assert rv.get_data() is not None
        funds_pull_pre_approval_id = rv.get_json()["funds_pull_pre_approval_id"]
        assert funds_pull_pre_approval_id == FUNDS_PULL_PRE_APPROVAL_ID

        assert len(calls) == 1
        call = calls[0]

        assert call["account_id"] == 1
        assert call["payer_address"] == request_body["payer_address"]
        assert call["description"] is None

        scope: offchain.FundPullPreApprovalScopeObject = call["scope"]
        assert scope.type == expected_scope["type"]
        assert scope.expiration_timestamp == expected_scope["expiration_timestamp"]
        assert scope.max_cumulative_amount is None
        assert scope.max_transaction_amount is None

    def test_wrong_timestamp_type(
        self, authorized_client: Client, mock_validation_tool_service
    ):
        """
        Sends request with wrong timestamp to make sure schema validation
        actually works.
        """
        expected_scope = {
            "type": "consent",
            "expiration_timestamp": "should be integer",
        }
        request_body = {
            "payer_address": "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc",
            "scope": expected_scope,
        }

        calls = mock_validation_tool_service(
            "request_funds_pull_pre_approval_from_another",
            will_return=(FUNDS_PULL_PRE_APPROVAL_ID, ADDRESS),
        )

        rv: Response = authorized_client.post(
            "/validation/funds_pull_pre_approvals",
            json=request_body,
        )

        assert rv.status_code == 400
        assert "expiration_timestamp" in rv.get_data(as_text=True)


class TestPreparePaymentAsReceiver:
    def test(self, authorized_client, mock_method):
        mock_method(
            validation_tool_service,
            "prepare_payment_as_receiver",
            will_return=(REFERENCE_ID, ADDRESS),
        )

        rv: Response = authorized_client.post(
            "/validation/payment_info/charge",
        )

        assert rv.status_code == 200
        assert rv.get_json()["address"] == ADDRESS
        assert rv.get_json()["reference_id"] == REFERENCE_ID
