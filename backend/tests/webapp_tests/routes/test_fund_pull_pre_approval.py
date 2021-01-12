from typing import List

import pytest
from flask import Response
from flask.testing import Client
from wallet.services import fund_pull_pre_approval as fppa_service
from wallet.services import offchain as offchain_service
from wallet.storage import models


FUNDS_PULL_PRE_APPROVAL_ID = "28992c81-e85a-4771-995a-af1d22bcaf63"
FUNDS_PULL_PRE_APPROVAL_ID_2 = "e1f7f846-f9e6-46f9-b184-c949f8d6b197"
BILLER_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
BILLER_ADDRESS_2 = "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc"
ADDRESS = "tdm1pwm5m35ayknjr0s67pk9xdf5mwp3nwq6ef67s55gpjwrqf"
ADDRESS_2 = "tdm1pztdjx2z8wp0q25jakqeklk0nxj2wmk2kg9whu8c3fdm9u"
CURRENCY = "XUS"


@pytest.fixture
def mock_get_funds_pull_pre_approvals(monkeypatch):
    def mock(account_id) -> List[models.FundsPullPreApprovalCommand]:
        funds_pull_pre_approval_1 = models.FundsPullPreApprovalCommand(
            account_id=1,
            address=ADDRESS,
            biller_address=BILLER_ADDRESS,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=1234,
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=100,
            max_cumulative_amount_currency=CURRENCY,
            max_transaction_amount=10,
            max_transaction_amount_currency=CURRENCY,
            description="bla la la",
            status="pending",
        )

        funds_pull_pre_approval_2 = models.FundsPullPreApprovalCommand(
            account_id=2,
            address=ADDRESS_2,
            biller_address=BILLER_ADDRESS_2,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID_2,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=1234,
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=100,
            max_cumulative_amount_currency=CURRENCY,
            max_transaction_amount=10,
            max_transaction_amount_currency=CURRENCY,
            description="bla la la",
            status="pending",
        )

        return [funds_pull_pre_approval_1, funds_pull_pre_approval_2]

    monkeypatch.setattr(fppa_service, "get_funds_pull_pre_approvals", mock)


class TestGetFundsPullPreApprovals:
    def test_get_funds_pull_pre_approvals(
        self, authorized_client: Client, mock_get_funds_pull_pre_approvals
    ) -> None:
        rv: Response = authorized_client.get(
            "/offchain/funds_pull_pre_approvals",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        funds_pull_pre_approvals = rv.get_json()["funds_pull_pre_approvals"]
        assert funds_pull_pre_approvals is not None
        assert len(funds_pull_pre_approvals) == 2
        assert funds_pull_pre_approvals[0]["biller_address"] == BILLER_ADDRESS


@pytest.fixture
def mock_successful_approve(monkeypatch):
    def mock(_funds_pull_pre_approval_id, _status) -> None:
        return None

    monkeypatch.setattr(fppa_service, "approve", mock)


@pytest.fixture
def mock_failed_approve(monkeypatch):
    def mock(_funds_pull_pre_approval_id, _status) -> None:
        raise fppa_service.FundsPullPreApprovalCommandNotFound

    monkeypatch.setattr(fppa_service, "approve", mock)


class TestApproveFundsPullPreApproval:
    def test_success(self, authorized_client: Client, mock_successful_approve):
        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PULL_PRE_APPROVAL_ID}",
            json={"funds_pull_pre_approval_id": "1234", "status": "bla"},
        )

        assert rv.status_code == 204

    def test_failure(self, authorized_client: Client, mock_failed_approve):
        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PULL_PRE_APPROVAL_ID}",
            json={"funds_pull_pre_approval_id": "1234", "status": "bla"},
        )

        assert rv.status_code == 404


@pytest.fixture
def mock_offchain_service(monkeypatch):
    def factory(method_name: str, will_return=None):
        calls = []

        def mock(**argv):
            calls.append(argv)
            return will_return

        monkeypatch.setattr(fppa_service, method_name, mock)
        return calls

    return factory


class TestCreateAndApprove:
    def test_success(self, authorized_client: Client, mock_offchain_service):
        request_body = {
            "biller_address": BILLER_ADDRESS,
            "funds_pull_pre_approval_id": FUNDS_PULL_PRE_APPROVAL_ID,
            "scope": {
                "type": "consent",
                "expiration_timestamp": 1234,
                "max_cumulative_amount": {
                    "unit": "week",
                    "value": 1,
                    "max_amount": {
                        "amount": 100,
                        "currency": CURRENCY,
                    },
                },
                "max_transaction_amount": {
                    "amount": 10,
                    "currency": CURRENCY,
                },
            },
            "description": "bla la la",
        }

        calls_to_create_and_approve = mock_offchain_service("create_and_approve")

        rv: Response = authorized_client.post(
            "/offchain/funds_pull_pre_approvals",
            json=request_body,
        )

        assert rv.status_code == 200

        assert len(calls_to_create_and_approve) == 1

        call = calls_to_create_and_approve[0]
        assert call.pop("account_id") == 1
        assert call.pop("biller_address") == request_body["biller_address"]
        assert (
            call.pop("funds_pull_pre_approval_id")
            == request_body["funds_pull_pre_approval_id"]
        )
        assert call.pop("funds_pull_pre_approval_type") == request_body["scope"]["type"]
        assert (
            call.pop("expiration_timestamp")
            == request_body["scope"]["expiration_timestamp"]
        )
        assert (
            call.pop("max_cumulative_unit")
            == request_body["scope"]["max_cumulative_amount"]["unit"]
        )
        assert (
            call.pop("max_cumulative_unit_value")
            == request_body["scope"]["max_cumulative_amount"]["value"]
        )
        assert (
            call.pop("max_cumulative_amount")
            == request_body["scope"]["max_cumulative_amount"]["max_amount"]["amount"]
        )
        assert (
            call.pop("max_cumulative_amount_currency")
            == request_body["scope"]["max_cumulative_amount"]["max_amount"]["currency"]
        )
        assert (
            call.pop("max_transaction_amount")
            == request_body["scope"]["max_transaction_amount"]["amount"]
        )
        assert (
            call.pop("max_transaction_amount_currency")
            == request_body["scope"]["max_transaction_amount"]["currency"]
        )
        assert call.pop("description") == request_body["description"]

        # Are there unexpected arguments?
        assert len(call) == 0


class TestOffchainV2View:
    def test_success(self, authorized_client: Client, monkeypatch):
        x_request_id = "f7ed63c3-eab9-4bd5-8094-497ba626e564"
        response_data = b"bond"

        def mock(sender_address, request_body):
            assert sender_address == ADDRESS
            assert request_body == b'{"dog": "gurki"}'

            return 200, response_data

        monkeypatch.setattr(offchain_service, "process_inbound_command", mock)

        rv: Response = authorized_client.post(
            "/offchain/v2/command",
            json={"dog": "gurki"},
            headers={"X-REQUEST-ID": x_request_id, "X-REQUEST-SENDER-ADDRESS": ADDRESS},
        )

        assert rv.status_code == 200
        assert rv.data == response_data
