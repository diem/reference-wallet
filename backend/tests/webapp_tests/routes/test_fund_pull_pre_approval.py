from datetime import datetime

import offchain
from offchain import FundPullPreApprovalStatus
from flask import Response
from flask.testing import Client
from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import TIMESTAMP
from wallet.services.offchain import (
    offchain as offchain_service,
    fund_pull_pre_approval as fppa_service,
)

FUNDS_PULL_PRE_APPROVAL_ID = "28992c81-e85a-4771-995a-af1d22bcaf63"
FUNDS_PULL_PRE_APPROVAL_ID_2 = "e1f7f846-f9e6-46f9-b184-c949f8d6b197"
BILLER_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
BILLER_ADDRESS_2 = "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc"
ADDRESS = "tdm1pwm5m35ayknjr0s67pk9xdf5mwp3nwq6ef67s55gpjwrqf"
ADDRESS_2 = "tdm1pztdjx2z8wp0q25jakqeklk0nxj2wmk2kg9whu8c3fdm9u"
CURRENCY = "XUS"


def invent_preapproval(description):
    return fppa_service.FPPAObject(
        my_actor_address=ADDRESS,
        funds_pull_pre_approval=offchain.FundPullPreApprovalObject(
            funds_pull_pre_approval_id=f"{BILLER_ADDRESS}_123",
            address=ADDRESS,
            biller_address=BILLER_ADDRESS,
            scope=offchain.FundPullPreApprovalScopeObject(
                type=offchain.FundPullPreApprovalType.consent,
                expiration_timestamp=TIMESTAMP,
                max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                    unit=offchain.TimeUnit.month,
                    value=1,
                    max_amount=offchain.CurrencyObject(
                        amount=111222333,
                        currency="XUS",
                    ),
                ),
                max_transaction_amount=offchain.CurrencyObject(
                    amount=111222333,
                    currency="XUS",
                ),
            ),
            status=FundPullPreApprovalStatus.pending,
            description=description,
        ),
        biller_name="Bond",
        created_timestamp=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        inbound=False,
    )


class TestGetFundsPullPreApprovals:
    def test_get_funds_pull_pre_approvals(
        self, authorized_client: Client, mock_method
    ) -> None:
        expected_len = 3
        expected_preapprovals = [
            invent_preapproval(str(i)) for i in range(expected_len)
        ]
        print(expected_preapprovals)
        calls = mock_method(
            fppa_service, "get_funds_pull_pre_approvals", expected_preapprovals
        )

        rv: Response = authorized_client.get(
            "/offchain/funds_pull_pre_approvals",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None

        assert len(calls) == 1
        assert calls[0][0] == 1  # account_id

        funds_pull_pre_approvals = rv.get_json()["funds_pull_pre_approvals"]
        assert funds_pull_pre_approvals is not None
        assert len(funds_pull_pre_approvals) == expected_len

        for i in range(expected_len):
            print(rv.get_json(), funds_pull_pre_approvals)
            assert funds_pull_pre_approvals[i]["description"] == str(i)


class TestUpdateFundPullPreApprovalStatus:
    def test_approve(self, authorized_client: Client, mock_method):
        calls = mock_method(fppa_service, "approve", will_return=None)

        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PULL_PRE_APPROVAL_ID}",
            json={
                "funds_pull_pre_approval_id": "1234",
                "status": FundPullPreApprovalStatus.valid,
            },
        )

        assert rv.status_code == 204
        assert len(calls) == 1
        assert calls[0][0] == FUNDS_PULL_PRE_APPROVAL_ID

    def test_reject(self, authorized_client: Client, mock_method):
        calls = mock_method(fppa_service, "reject", will_return=None)

        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PULL_PRE_APPROVAL_ID}",
            json={
                "funds_pull_pre_approval_id": "1234",
                "status": FundPullPreApprovalStatus.rejected,
            },
        )

        assert rv.status_code == 204
        assert len(calls) == 1
        assert calls[0][0] == FUNDS_PULL_PRE_APPROVAL_ID

    def test_close(self, authorized_client: Client, mock_method):
        calls = mock_method(fppa_service, "close", will_return=None)

        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PULL_PRE_APPROVAL_ID}",
            json={
                "funds_pull_pre_approval_id": "1234",
                "status": FundPullPreApprovalStatus.closed,
            },
        )

        assert rv.status_code == 204
        assert len(calls) == 1
        assert calls[0][0] == FUNDS_PULL_PRE_APPROVAL_ID

    def test_failure(self, authorized_client: Client, mock_method):
        calls = mock_method(
            fppa_service,
            "approve",
            will_raise=fppa_service.FundsPullPreApprovalCommandNotFound,
        )

        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PULL_PRE_APPROVAL_ID}",
            json={
                "funds_pull_pre_approval_id": "1234",
                "status": FundPullPreApprovalStatus.valid,
            },
        )

        assert rv.status_code == 404
        assert len(calls) == 1
        assert calls[0][0] == FUNDS_PULL_PRE_APPROVAL_ID


class TestCreateAndApprove:
    def test_success(self, authorized_client: Client, mock_method):
        request_body = {
            "biller_address": BILLER_ADDRESS,
            "funds_pull_pre_approval_id": FUNDS_PULL_PRE_APPROVAL_ID,
            "scope": {
                "type": "consent",
                "expiration_timestamp": TIMESTAMP,
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

        calls_to_create_and_approve = mock_method(fppa_service, "create_and_approve")

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
