import json
import uuid
from typing import Optional, List

import context
import pytest
from diem import offchain
from flask import Response
from flask.testing import Client
from wallet.services import offchain as offchain_service
from wallet.storage import FundsPullPreApprovalCommands

FUNDS_PRE_APPROVAL_ID = "28992c81-e85a-4771-995a-af1d22bcaf63"
FUNDS_PRE_APPROVAL_ID_2 = "e1f7f846-f9e6-46f9-b184-c949f8d6b197"
BILLER_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
BILLER_ADDRESS_2 = "tdm1pvjua68j72mhmp3n7jkuthmxlkj0g57gkpegq6qgkjfxwc"
ADDRESS = "tdm1pwm5m35ayknjr0s67pk9xdf5mwp3nwq6ef67s55gpjwrqf"
ADDRESS_2 = "tdm1pztdjx2z8wp0q25jakqeklk0nxj2wmk2kg9whu8c3fdm9u"
CURRENCY = "XUS"


@pytest.fixture
def mock_get_payment_command_json(monkeypatch):
    def mock(transaction_id: int) -> Optional[str]:
        return json.loads(
            '{"my_actor_address": "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "payment": {'
            '"reference_id": "c6f7e351-e1c3-4da7-9310-4e87296febf2", "sender": {"address": '
            '"tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "status": {"status": "ready_for_settlement"}, '
            '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "3qflfqmo", "surname": '
            '"yph277u8", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
            '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "receiver": {"address": '
            '"tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd", "status": {"status": "ready_for_settlement"}, '
            '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "gug0fngi", "surname": '
            '"6mpcox8c", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
            '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "action": {"amount": 2000000000, '
            '"currency": "XUS", "action": "charge", "timestamp": 1609064370}, "recipient_signature": '
            '"ce9daec5599dc5afd5955d45664cb07be4e2104e32034b8356c3f0e99782d86288ed735d5ac3ffd6b08bba78a001e1b084284453a09400e1e1cbae9a9ac0d108"}, "inbound": false, "cid": "1cea3243-4ea6-44b2-8590-ec5bf4a101b1"} '
        )

    monkeypatch.setattr(offchain_service, "get_payment_command_json", mock)


class TestGetPaymentCommand:
    def test_get_payment_command_json(
        self, authorized_client: Client, mock_get_payment_command_json
    ) -> None:
        rv: Response = authorized_client.get(
            "/offchain/query/payment_command/22",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        payment_command = rv.get_json()["payment_command"]
        assert payment_command is not None
        assert payment_command["my_actor_address"] == BILLER_ADDRESS


@pytest.fixture
def mock_get_account_payment_commands(monkeypatch):
    def mock(account_id: int) -> List[str]:
        return [
            json.loads(
                '{"my_actor_address": "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "payment": {"reference_id": '
                '"c6f7e351-e1c3-4da7-9310-4e87296febf2", "sender": {"address": '
                '"tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "3qflfqmo", "surname": '
                '"yph277u8", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "receiver": {"address": '
                '"tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "gug0fngi", "surname": '
                '"6mpcox8c", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "action": {"amount": 2000000000, '
                '"currency": "XUS", "action": "charge", "timestamp": 1609064370}, "recipient_signature": '
                '"ce9daec5599dc5afd5955d45664cb07be4e2104e32034b8356c3f0e99782d86288ed735d5ac3ffd6b08bba78a001e1b084284453a09400e1e1cbae9a9ac0d108"}, '
                '"inbound": false, "cid": "1cea3243-4ea6-44b2-8590-ec5bf4a101b1"}'
            ),
            json.loads(
                '{"my_actor_address": "tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5", "payment": {"reference_id": '
                '"dbcb698a-22a8-4dac-8710-668cdfdd045e", "sender": {"address": '
                '"tdm1pwm5m35ayknjr0s67pk9xdf5mwp3nwq6ef67s55gpjwrqf", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "wb5xaftc", "surname": '
                '"aaogh8rp", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "receiver": {"address": '
                '"tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5", "status": {"status": "ready_for_settlement"}, '
                '"kyc_data": {"type": "individual", "payload_version": 1, "given_name": "nz45p518", "surname": '
                '"qs83qard", "address": {"city": "London", "country": "GB", "line1": "221B Baker Street", "line2": "", '
                '"postal_code": "NW1 6XE", "state": ""}, "dob": "1861-06-01"}}, "action": {"amount": 2000000000, '
                '"currency": "XUS", "action": "charge", "timestamp": 1609064361}, "recipient_signature": '
                '"d84c2e733c9d68c869ad5e2bb155e8f5441c65312d47dfd5189abfb5037a160dcca770cd733284bae53847c0d6eb17afc31248453a7fcbe43c5b2f3eadd67208"}, '
                '"inbound": true, "cid": "3b6f2e01-2da0-4acb-ad74-631546edfba0"}'
            ),
        ]

    monkeypatch.setattr(offchain_service, "get_account_payment_commands", mock)


class TestGetAccountPaymentCommands:
    def test_get_account_payment_commands(
        self, authorized_client: Client, mock_get_account_payment_commands
    ) -> None:
        rv: Response = authorized_client.get(
            "/offchain/query/payment_command",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        payment_commands = rv.get_json()["payment_commands"]
        assert payment_commands is not None
        assert len(payment_commands) == 2
        assert payment_commands[0]["my_actor_address"] == BILLER_ADDRESS


@pytest.fixture
def mock_get_funds_pull_pre_approvals(monkeypatch):
    def mock(account_id) -> List[FundsPullPreApprovalCommands]:
        funds_pull_pre_approval_1 = FundsPullPreApprovalCommands(
            account_id=1,
            address=ADDRESS,
            biller_address=BILLER_ADDRESS,
            funds_pre_approval_id=FUNDS_PRE_APPROVAL_ID,
            scope_type="consent",
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

        funds_pull_pre_approval_2 = FundsPullPreApprovalCommands(
            account_id=2,
            address=ADDRESS_2,
            biller_address=BILLER_ADDRESS_2,
            funds_pre_approval_id=FUNDS_PRE_APPROVAL_ID_2,
            scope_type="consent",
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

    monkeypatch.setattr(offchain_service, "get_funds_pull_pre_approvals", mock)


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
def mock_successful_approve_funds_pull_pre_approval(monkeypatch):
    def mock(funds_pre_approval_id, status) -> None:
        return None

    monkeypatch.setattr(offchain_service, "approve_funds_pull_pre_approval", mock)


@pytest.fixture
def mock_failed_approve_funds_pull_pre_approval(monkeypatch):
    def mock(funds_pre_approval_id, status) -> None:
        raise offchain_service.FundsPullPreApprovalCommandNotFound

    monkeypatch.setattr(offchain_service, "approve_funds_pull_pre_approval", mock)


class TestApproveFundsPullPreApproval:
    def test_successful_get_funds_pull_pre_approvals(
        self, authorized_client: Client, mock_successful_approve_funds_pull_pre_approval
    ) -> None:
        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PRE_APPROVAL_ID}",
            json={"funds_pre_approval_id": "1234", "status": "bla"},
        )

        assert rv.status_code == 204

    def test_failed_get_funds_pull_pre_approvals(
        self, authorized_client: Client, mock_failed_approve_funds_pull_pre_approval
    ) -> None:
        rv: Response = authorized_client.put(
            f"/offchain/funds_pull_pre_approvals/{FUNDS_PRE_APPROVAL_ID}",
            json={"funds_pre_approval_id": "1234", "status": "bla"},
        )

        assert rv.status_code == 404


@pytest.fixture
def mock_establish_funds_pull_pre_approval(monkeypatch):
    def mock(
        account_id,
        biller_address,
        funds_pre_approval_id,
        scope_type,
        expiration_timestamp,
        max_cumulative_unit,
        max_cumulative_unit_value,
        max_cumulative_amount,
        max_cumulative_amount_currency,
        max_transaction_amount,
        max_transaction_amount_currency,
        description,
    ) -> None:
        return None

    monkeypatch.setattr(offchain_service, "establish_funds_pull_pre_approval", mock)


class TestEstablishFundsPullPreApproval:
    def test_establish_funds_pull_pre_approval(
        self, authorized_client: Client, mock_establish_funds_pull_pre_approval
    ) -> None:
        rv: Response = authorized_client.post(
            "/offchain/funds_pull_pre_approvals",
            json={
                "account_id": 1,
                "biller_address": BILLER_ADDRESS,
                "funds_pre_approval_id": FUNDS_PRE_APPROVAL_ID,
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
            },
        )

        assert rv.status_code == 200
