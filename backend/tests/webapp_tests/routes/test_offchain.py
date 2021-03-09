import uuid
from typing import Optional, List
from datetime import datetime

import pytest
from flask import Response
from flask.testing import Client
from wallet.services.offchain import payment_command as pc_service
from diem import offchain

CURRENCY = "XUS"
ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"


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

    monkeypatch.setattr(pc_service, "get_payment_command", mock)


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

    monkeypatch.setattr(pc_service, "get_account_payment_commands", mock)


@pytest.fixture()
def mock_add_payment_command(monkeypatch):
    def mock(
        account_id,
        reference_id,
        vasp_address,
        merchant_name,
        action,
        currency,
        amount,
        expiration,
    ) -> None:
        return

    monkeypatch.setattr(pc_service, "add_payment_command", mock)


@pytest.fixture()
def mock_update_payment_command_status(monkeypatch):
    def mock(reference_id, status) -> None:
        return

    monkeypatch.setattr(pc_service, "update_payment_command_status", mock)


class TestGetPaymentCommand:
    def test_get_payment_command_json(
        self, authorized_client: Client, mock_get_payment_command_json
    ) -> None:
        rv: Response = authorized_client.get(
            "/offchain/query/payment_command/22",
        )

        assert rv.status_code == 200
        assert rv.get_data() is not None
        payment_object = rv.get_json()["payment"]
        assert payment_object is not None
        assert (
            rv.get_json()["my_actor_address"]
            == "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
        )


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
        assert (
            payment_commands[0]["my_actor_address"]
            == "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
        )


class TestAddPaymentCommand:
    def test_add_payment_command(
        self, authorized_client: Client, mock_add_payment_command
    ) -> None:
        rv: Response = authorized_client.post(
            "/offchain/payment_command",
            json={
                "vasp_address": "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
                "reference_id": str(uuid.uuid4()),
                "merchant_name": "Bond & Gurki Pet Store",
                "action": "charge",
                "currency": "XUS",
                "amount": 1000,
                "expiration": int(datetime.timestamp(datetime.now())),
                "redirect_url": "https://bondandgurki.com/order/93c4963f-7f9e-4f9d-983e-7080ef782534/checkout/complete",
            },
        )

        assert rv.status_code == 204, rv.get_data()


class TestUpdatePaymentCommandStatus:
    def test_update_payment_command_status(
        self, authorized_client: Client, mock_update_payment_command_status
    ) -> None:
        rv: Response = authorized_client.put(
            "/offchain/payment_command/1234",
            json={
                "status": "needs_kyc_data",
            },
        )

        assert rv.status_code == 204, rv.get_data()
