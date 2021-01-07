import json
from typing import Optional, List

import pytest
from flask import Response
from flask.testing import Client
from wallet.services import offchain as offchain_service
from wallet.storage import FundsPullPreApprovalCommands
from diem import offchain

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
        return offchain.PaymentCommand(
            my_actor_address="tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
            payment=offchain.PaymentObject(
                reference_id="c6f7e351-e1c3-4da7-9310-4e87296febf2",
                sender=offchain.PaymentActorObject(
                    address="tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
                    status=offchain.StatusObject(status="ready_for_settlement"),
                    kyc_data=offchain.KycDataObject(
                        type="individual",
                        payload_version=1,
                        given_name="Bond",
                        surname="Marton",
                        address=offchain.AddressObject(
                            city="Dogcity",
                            country="Dogland",
                            line1="1234 Puppy Street",
                            line2="dogpalace 3",
                            postal_code="123456",
                            state="",
                        ),
                        dob="2010-21-01",
                    ),
                    additional_kyc_data="",
                    metadata=[],
                ),
                receiver=offchain.PaymentActorObject(
                    address="tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd",
                    status=offchain.StatusObject(status="ready_for_settlement"),
                    kyc_data=offchain.KycDataObject(
                        type="individual",
                        payload_version=1,
                        given_name="Gurki",
                        surname="Silver",
                        address=offchain.AddressObject(
                            city="Dogcity",
                            country="Dogland",
                            line1="567 Puppy Street",
                            line2="doggarden 3",
                            postal_code="123456",
                            state="",
                        ),
                        dob="2011-11-11",
                    ),
                    additional_kyc_data="",
                    metadata=[],
                ),
                action=offchain.PaymentActionObject(
                    amount=2000000000,
                    currency="XUS",
                    action="charge",
                    timestamp=1609064370,
                ),
                recipient_signature="ce9daec5599dc5afd5955d45664cb07be4e2104e32034b8356c3f0e99782d86288ed735d5ac3ffd6b08bba78a001e1b084284453a09400e1e1cbae9a9ac0d108",
                original_payment_reference_id="",
                description="",
            ),
            inbound=False,
            cid="1cea3243-4ea6-44b2-8590-ec5bf4a101b1",
        )

    monkeypatch.setattr(offchain_service, "get_payment_command", mock)


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
            offchain.PaymentCommand(
                my_actor_address="tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
                payment=offchain.PaymentObject(
                    reference_id="c6f7e351-e1c3-4da7-9310-4e87296febf2",
                    sender=offchain.PaymentActorObject(
                        address="tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
                        status=offchain.StatusObject(status="ready_for_settlement"),
                        kyc_data=offchain.KycDataObject(
                            type="individual",
                            payload_version=1,
                            given_name="Bond",
                            surname="Marton",
                            address=offchain.AddressObject(
                                city="Dogcity",
                                country="Dogland",
                                line1="1234 Puppy Street",
                                line2="dogpalace 3",
                                postal_code="123456",
                                state="",
                            ),
                            dob="2010-21-01",
                        ),
                        additional_kyc_data="",
                        metadata=[],
                    ),
                    receiver=offchain.PaymentActorObject(
                        address="tdm1pwm5m35ayknjr0s67pk9xdf5mwqft4rvgxplmckcxr9lwd",
                        status=offchain.StatusObject(status="ready_for_settlement"),
                        kyc_data=offchain.KycDataObject(
                            type="individual",
                            payload_version=1,
                            given_name="Gurki",
                            surname="Silver",
                            address=offchain.AddressObject(
                                city="Dogcity",
                                country="Dogland",
                                line1="567 Puppy Street",
                                line2="doggarden 3",
                                postal_code="123456",
                                state="",
                            ),
                            dob="2011-11-11",
                        ),
                        additional_kyc_data="",
                        metadata=[],
                    ),
                    action=offchain.PaymentActionObject(
                        amount=2000000000,
                        currency="XUS",
                        action="charge",
                        timestamp=1609064370,
                    ),
                    recipient_signature="ce9daec5599dc5afd5955d45664cb07be4e2104e32034b8356c3f0e99782d86288ed735d5ac3ffd6b08bba78a001e1b084284453a09400e1e1cbae9a9ac0d108",
                    original_payment_reference_id="",
                    description="",
                ),
                inbound=False,
                cid="1cea3243-4ea6-44b2-8590-ec5bf4a101b1",
            ),
            offchain.PaymentCommand(
                my_actor_address="tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5",
                payment=offchain.PaymentObject(
                    reference_id="dbcb698a-22a8-4dac-8710-668cdfdd045e",
                    sender=offchain.PaymentActorObject(
                        address="tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5",
                        status=offchain.StatusObject(status="ready_for_settlement"),
                        kyc_data=offchain.KycDataObject(
                            type="individual",
                            payload_version=1,
                            given_name="Bond",
                            surname="Marton",
                            address=offchain.AddressObject(
                                city="Dogcity",
                                country="Dogland",
                                line1="1234 Puppy Street",
                                line2="dogpalace 3",
                                postal_code="123456",
                                state="",
                            ),
                            dob="2010-21-01",
                        ),
                        additional_kyc_data="",
                        metadata=[],
                    ),
                    receiver=offchain.PaymentActorObject(
                        address="tdm1pzmhcxpnyns7m035ctdqmexxadxjjalh3xckacksflqvx5",
                        status=offchain.StatusObject(status="ready_for_settlement"),
                        kyc_data=offchain.KycDataObject(
                            type="individual",
                            payload_version=1,
                            given_name="Gurki",
                            surname="Silver",
                            address=offchain.AddressObject(
                                city="Dogcity",
                                country="Dogland",
                                line1="567 Puppy Street",
                                line2="doggarden 3",
                                postal_code="123456",
                                state="",
                            ),
                            dob="2011-11-11",
                        ),
                        additional_kyc_data="",
                        metadata=[],
                    ),
                    action=offchain.PaymentActionObject(
                        amount=2000000000,
                        currency="XUS",
                        action="charge",
                        timestamp=1609064370,
                    ),
                    recipient_signature="d84c2e733c9d68c869ad5e2bb155e8f5441c65312d47dfd5189abfb5037a160dcca770cd733284bae53847c0d6eb17afc31248453a7fcbe43c5b2f3eadd67208",
                    original_payment_reference_id="",
                    description="",
                ),
                inbound=False,
                cid="1cea3243-4ea6-44b2-8590-ec5bf4a101b1",
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

        funds_pull_pre_approval_2 = FundsPullPreApprovalCommands(
            account_id=2,
            address=ADDRESS_2,
            biller_address=BILLER_ADDRESS_2,
            funds_pre_approval_id=FUNDS_PRE_APPROVAL_ID_2,
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
    def mock(_funds_pre_approval_id, _status) -> None:
        return None

    monkeypatch.setattr(offchain_service, "approve_funds_pull_pre_approval", mock)


@pytest.fixture
def mock_failed_approve_funds_pull_pre_approval(monkeypatch):
    def mock(_funds_pre_approval_id, _status) -> None:
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
        account_id: int,
        biller_address: str,
        funds_pre_approval_id: str,
        funds_pull_pre_approval_type: str,
        expiration_timestamp: int,
        max_cumulative_unit: str = None,
        max_cumulative_unit_value: int = None,
        max_cumulative_amount: int = None,
        max_cumulative_amount_currency: str = None,
        max_transaction_amount: int = None,
        max_transaction_amount_currency: str = None,
        description: str = None,
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


class TestOffchainV2View:
    def test_process_inbound_command(
        self, authorized_client: Client, monkeypatch
    ) -> None:
        x_request_id = "f7ed63c3-eab9-4bd5-8094-497ba626e564"
        response_data = b"bond"

        def mock(_sender_address, _request_body):
            assert _sender_address == ADDRESS
            assert _request_body == b'{"dog": "gurki"}'

            return 200, response_data

        monkeypatch.setattr(offchain_service, "process_inbound_command", mock)

        rv: Response = authorized_client.post(
            "/offchain/v2/command",
            json={"dog": "gurki"},
            headers={"X-REQUEST-ID": x_request_id, "X-REQUEST-SENDER-ADDRESS": ADDRESS},
        )

        assert rv.status_code == 200
        assert rv.data == response_data
