# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import diem_utils.types.currencies
from tests.wallet_tests.resources.seeds.one_user_multiple_transactions import (
    OneUserMultipleTransactions,
)
import pytest
from wallet import types
from wallet.storage import (
    db_session,
    get_account_transaction_ids,
    add_user,
    Transaction,
    get_user_transactions,
    add_transaction,
    get_user,
)
from wallet.types import RegistrationStatus


def test_create_user() -> None:
    username = "fake_username"
    password_hash = "fake_hash"
    salt = "fake_salt"
    user_id = add_user(
        username=username,
        password_hash=password_hash,
        salt=salt,
        registration_status=RegistrationStatus.Pending,
    )

    storage_user = get_user(username=username)
    assert storage_user
    assert storage_user.id == user_id


def test_add_transaction() -> None:
    tx = add_transaction(
        amount=100,
        currency=diem_utils.types.currencies.DiemCurrency.Coin1,
        payment_type=types.TransactionType.EXTERNAL,
        status=types.TransactionStatus.PENDING,
        source_id=1,
        source_address="sender_address",
        source_subaddress="sender_subaddress",
        destination_id=123,
        destination_address="receiver_address",
        destination_subaddress="receiver_subaddress",
    )
    assert tx.id in get_account_transaction_ids(1)


def test_add_faulty_offchain_transaction() -> None:
    with pytest.raises(ValueError):
        add_transaction(
            amount=100,
            currency=diem_utils.types.currencies.DiemCurrency.Coin1,
            payment_type=types.TransactionType.OFFCHAIN,
            status=types.TransactionStatus.PENDING,
            source_id=1,
            source_address="sender_address",
            source_subaddress="sender_subaddress",
            destination_id=123,
            destination_address="receiver_address",
            destination_subaddress="receiver_subaddress",
        )


def test_get_user_transactions() -> None:
    tx1, tx2, user = OneUserMultipleTransactions().run(db_session)

    tx_list = get_user_transactions(user.id)

    assert len(tx_list) == OneUserMultipleTransactions.total_txs


def test_get_user_transactions_for_coin() -> None:
    tx1, tx2, user = OneUserMultipleTransactions().run(db_session)

    tx_list = get_user_transactions(user.id, OneUserMultipleTransactions.tx1_currency)

    assert len(tx_list) == 2
    tx: Transaction = tx_list[0]
    assert tx.currency == OneUserMultipleTransactions.tx1_currency
