# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from datetime import datetime
from http import HTTPStatus
from typing import Optional

import pytest
from offchain import Status, AddressObject
from flask import Response
from wallet.services.transaction import FundsTransfer
from werkzeug import Client

from diem_utils.types.currencies import DiemCurrency
from wallet.services import account as account_service
from wallet.services import transaction as transaction_service
from wallet.storage import Transaction
from wallet.types import (
    Balance,
    TransactionDirection,
    TransactionStatus,
    TransactionType,
    TransactionSortOption,
)
import offchain

INTERNAL_TX = Transaction(
    id=1,
    type=TransactionType.INTERNAL.value,
    amount=100,
    currency=DiemCurrency.XUS.value,
    status=TransactionStatus.COMPLETED.value,
    source_id=1,
    source_address="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    source_subaddress="863bc063df8b2bf3",
    destination_id=2,
    destination_address="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    destination_subaddress="75b12ccd3ab503a6",
    created_timestamp=datetime.fromisoformat("2020-06-23T19:49:26.989849"),
)
INTERNAL_FUNDS_TRANSFER = FundsTransfer(
    transaction=Transaction(
        id=1,
        type=TransactionType.INTERNAL.value,
        amount=100,
        currency=DiemCurrency.XUS.value,
        status=TransactionStatus.COMPLETED.value,
        source_id=1,
        source_address="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        source_subaddress="863bc063df8b2bf3",
        destination_id=2,
        destination_address="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        destination_subaddress="75b12ccd3ab503a6",
        created_timestamp=datetime.fromisoformat("2020-06-23T19:49:26.989849"),
    ),
    payment_command=offchain.PaymentCommand(
        my_actor_address="tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
        payment=offchain.PaymentObject(
            reference_id="c6f7e351-e1c3-4da7-9310-4e87296febf2",
            sender=offchain.PaymentActorObject(
                address="tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp",
                status=offchain.StatusObject(status=Status.ready_for_settlement),
                kyc_data=offchain.KycDataObject(
                    type="individual",
                    payload_version=1,
                    given_name="Bond",
                    surname="Marton",
                    address=AddressObject.new_address_object(
                        city="Dogcity",
                        country="DL",
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
                status=offchain.StatusObject(status=Status.ready_for_settlement),
                kyc_data=offchain.KycDataObject(
                    type="individual",
                    payload_version=1,
                    given_name="Gurki",
                    surname="Silver",
                    address=AddressObject.new_address_object(
                        city="Dogcity",
                        country="DL",
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
)
FULL_ADDRESS = "tdm1pztdjx2z8wp0q25jakqeklk0nxj2wmk2kg9whu8c3fdm9u"


@pytest.fixture
def allow_user_to_account(monkeypatch):
    monkeypatch.setattr(
        account_service, "is_user_allowed_for_account", lambda user, account_name: True
    )


@pytest.fixture
def account_balance(monkeypatch):
    saved = {}

    def get_account_balance_mock(account_name: str):
        saved["account_name"] = account_name
        balance = Balance()
        balance.total = {DiemCurrency.XUS: 100}
        return balance

    monkeypatch.setattr(
        account_service, "get_account_balance_by_name", get_account_balance_mock
    )
    yield saved


@pytest.fixture
def account_transactions_mock(monkeypatch):
    saved = {}

    def get_mock(
        account_id: Optional[int] = None,
        account_name: Optional[str] = None,
        currency: Optional[DiemCurrency] = None,
        direction_filter: Optional[TransactionDirection] = None,
        limit: Optional[int] = None,
        sort: Optional[TransactionSortOption] = None,
    ):
        saved["account_id"] = account_id
        saved["account_name"] = account_name
        saved["currency"] = currency
        return [INTERNAL_TX]

    monkeypatch.setattr(account_service, "get_account_transactions", get_mock)
    yield saved


@pytest.fixture
def get_transaction_by_id_mock(monkeypatch):
    saved = {}

    def mock(reference_id: str) -> FundsTransfer:
        saved["transaction_id"] = reference_id
        if reference_id == "1":
            return INTERNAL_FUNDS_TRANSFER
        funds_transfer = deepcopy(INTERNAL_FUNDS_TRANSFER)
        funds_transfer.transaction.source_id = 3
        return funds_transfer

    monkeypatch.setattr(transaction_service, "get_funds_transfer", mock)
    yield saved


@pytest.fixture
def send_transaction_mock(monkeypatch):
    saved = {}

    def send_mock(
        sender_id: int,
        amount: int,
        currency: DiemCurrency,
        destination_address: str,
        destination_subaddress: Optional[str] = None,
        payment_type: Optional[TransactionType] = None,
    ) -> Optional[int]:
        saved.update(
            {
                "sender_id": sender_id,
                "amount": amount,
                "currency": currency,
                "destination_address": destination_address,
                "destination_subaddress": destination_subaddress,
                "payment_type": payment_type,
            }
        )
        return 5

    monkeypatch.setattr(transaction_service, "send_transaction", send_mock)
    yield saved


@pytest.fixture
def get_deposit_address_mock(monkeypatch):
    monkeypatch.setattr(
        account_service,
        "get_deposit_address",
        lambda account_id=None, account_name=None: FULL_ADDRESS,
    )


class TestAccountInfo:
    def test_get_account_info(
        self, authorized_client: Client, allow_user_to_account, account_balance
    ) -> None:
        rv: Response = authorized_client.get(
            "/account",
        )
        assert rv.status_code == 200
        balances = rv.get_json()["balances"]
        assert account_balance["account_name"] == "fake_account"
        assert len(balances) == 1
        assert balances[0]["currency"] == DiemCurrency.XUS.value
        assert balances[0]["balance"] == 100


class TestAccountTransactions:
    def test_get_transaction_by_id(
        self,
        authorized_client: Client,
        allow_user_to_account,
        get_transaction_by_id_mock,
    ) -> None:
        rv: Response = authorized_client.get(
            "/account/transactions/1",
        )
        assert rv.status_code == 200, rv.data
        funds_transfer = rv.get_json()
        assert funds_transfer["transaction"] == {
            "id": 1,
            "amount": 100,
            "currency": DiemCurrency.XUS.value,
            "direction": TransactionDirection.SENT.value,
            "status": TransactionStatus.COMPLETED.value,
            "timestamp": "2020-06-23T19:49:26.989849",
            "source": {
                "full_addr": "tdm1p42424242424242424242424242rrhsrrm79jhuckttdwm",
                "user_id": "863bc063df8b2bf3",
                "vasp_name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            },
            "destination": {
                "full_addr": "tdm1p4242424242424242424242424f6mztxd826s8fs796d0f",
                "user_id": "75b12ccd3ab503a6",
                "vasp_name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            },
            "blockchain_tx": None,
            "is_internal": True,
            "reference_id": None,
        }

    def test_get_transaction_by_id_other_user(
        self,
        authorized_client: Client,
        allow_user_to_account,
        get_transaction_by_id_mock,
    ) -> None:
        rv: Response = authorized_client.get(
            "/account/transactions/2",
        )
        assert get_transaction_by_id_mock["transaction_id"] == "2"
        assert rv.status_code == 404

    def test_get_account_transactions(
        self,
        authorized_client: Client,
        allow_user_to_account,
        account_transactions_mock,
    ) -> None:
        rv: Response = authorized_client.get(
            "/account/transactions",
        )
        assert rv.status_code == 200
        transactions = rv.get_json()
        assert len(transactions) == 1
        assert transactions["transaction_list"] == [
            {
                "id": 1,
                "amount": 100,
                "currency": DiemCurrency.XUS.value,
                "direction": TransactionDirection.SENT.value,
                "status": TransactionStatus.COMPLETED.value,
                "timestamp": "2020-06-23T19:49:26.989849",
                "source": {
                    "full_addr": "tdm1p42424242424242424242424242rrhsrrm79jhuckttdwm",
                    "user_id": "863bc063df8b2bf3",
                    "vasp_name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                },
                "destination": {
                    "full_addr": "tdm1p4242424242424242424242424f6mztxd826s8fs796d0f",
                    "user_id": "75b12ccd3ab503a6",
                    "vasp_name": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                },
                "blockchain_tx": None,
                "is_internal": True,
                "reference_id": None,
            }
        ]

    def test_get_account_transactions_by_currency(
        self,
        authorized_client: Client,
        allow_user_to_account,
        account_transactions_mock,
    ) -> None:
        requested_currency = DiemCurrency.XUS.value
        rv: Response = authorized_client.get(
            f"/account/transactions?currency={requested_currency}"
        )
        assert rv.status_code == 200
        transactions = rv.get_json()
        assert len(transactions) == 1
        assert account_transactions_mock["currency"] == requested_currency


class TestSendTransaction:
    currency = DiemCurrency.XUS.value
    amount = 100
    receiver_address, receiver_subaddress = (
        "12db232847705e05525db0336fd9f334",
        "94edd956415d7e1f",
    )
    receiver_full_address = "tdm1pztdjx2z8wp0q25jakqeklk0nxj2wmk2kg9whu8c3fdm9u"
    tx_data = {
        "currency": currency,
        "amount": amount,
        "receiver_address": receiver_full_address,
    }

    def test_send_transaction(
        self, authorized_client: Client, allow_user_to_account, send_transaction_mock
    ) -> None:
        rv: Response = authorized_client.post(
            "/account/transactions", json=TestSendTransaction.tx_data
        )
        assert rv.status_code == 200
        assert rv.get_json()["id"] == 5

    def test_send_transaction_risk_error(self, authorized_client: Client, monkeypatch):
        def send_transaction_mock_risk_failure(
            sender_id: int,
            amount: int,
            currency: DiemCurrency,
            destination_address: str,
            destination_subaddress: Optional[str] = None,
            payment_type: Optional[TransactionType] = None,
        ) -> Optional[Transaction]:
            raise transaction_service.RiskCheckError("Risk!")

        monkeypatch.setattr(
            transaction_service, "send_transaction", send_transaction_mock_risk_failure
        )

        rv: Response = authorized_client.post(
            "/account/transactions", json=TestSendTransaction.tx_data
        )
        assert rv.status_code == HTTPStatus.FAILED_DEPENDENCY

    def test_send_transaction_to_self_error(
        self, authorized_client: Client, monkeypatch
    ):
        def send_transaction_mock_self_as_destination_failure(
            sender_id: int,
            amount: int,
            currency: DiemCurrency,
            destination_address: str,
            destination_subaddress: Optional[str] = None,
            payment_type: Optional[TransactionType] = None,
        ) -> Optional[Transaction]:
            raise transaction_service.SelfAsDestinationError("Don't send to self!")

        monkeypatch.setattr(
            transaction_service,
            "send_transaction",
            send_transaction_mock_self_as_destination_failure,
        )

        rv: Response = authorized_client.post(
            "/account/transactions", json=TestSendTransaction.tx_data
        )
        assert rv.status_code == HTTPStatus.FORBIDDEN


class TestGetReceivingAddresses:
    def test_get_receiving_addresses(
        self, authorized_client: Client, allow_user_to_account, get_deposit_address_mock
    ) -> None:
        rv: Response = authorized_client.post("/account/receiving-addresses")
        print(rv.data)
        assert rv.status_code == 200
        assert rv.get_json() == {"address": FULL_ADDRESS}
