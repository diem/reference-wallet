# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pylibra import LibraNetwork

import libra_utils.types.currencies
from libra_utils.types.metadata import MetadataType
from libra_utils.custody import Custody
from libra_utils.libra import encode_subaddr, wait_for_account_seq
from libra_utils.types.currencies import LibraCurrency
from pubsub.types import TransactionMetadata
from tests.wallet_tests.pylibra_mocks import AccountMocker
from tests.wallet_tests.resources.seeds.balances_seeder import BalancesSeeder
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet import storage, types
from wallet.services.account import (
    calc_account_balance,
    create_account,
    generate_new_subaddress,
)
from wallet.services.transaction import (
    send_transaction,
    get_transaction_direction,
    process_incoming_transaction,
    get_transaction,
    RiskCheckError,
    SelfAsDestinationError,
    get_total_balance,
)
from wallet.storage import (
    get_account_transaction_ids,
    get_single_transaction,
    get_account_id_from_subaddr,
    Transaction,
    db_session,
)
from wallet.types import TransactionDirection, TransactionType, TransactionStatus


def test_send_transaction() -> None:
    account_id, send_tx = send_fake_tx()
    assert send_tx.id in get_account_transaction_ids(account_id)

    tx = get_single_transaction(send_tx.id)
    assert tx.source_id == account_id
    assert tx.destination_address == "receiver_address"
    assert tx.destination_subaddress == "receiver_subaddress"


def test_transaction_direction(no_background_tasks) -> None:
    account_id, send_tx = send_fake_tx()
    assert get_transaction_direction(account_id, send_tx) == TransactionDirection.SENT


def test_send_transaction_risk_check_error() -> None:
    with pytest.raises(RiskCheckError) as risk_check_error:
        send_fake_tx(amount=1_000 * 1_000_000 + 1)


def test_send_tx_to_self_error() -> None:
    with pytest.raises(SelfAsDestinationError):
        send_fake_tx(send_to_self=True)


def test_subaddr_map() -> None:
    account = create_account(account_name="fake_account")

    subaddr = generate_new_subaddress(account.id)

    assert get_account_id_from_subaddr(subaddr) == account.id


def test_transaction_seq_exist() -> None:
    source_addr = "fake_source_addr"
    source_subaddr = "fake_source_subaddr"
    assert not storage.get_transaction_by_details(
        source_address=source_addr, source_subaddress=source_subaddr, sequence=0
    )
    storage.add_transaction(
        amount=100,
        currency=LibraCurrency.Coin1,
        payment_type=TransactionType.INTERNAL,
        status=TransactionStatus.COMPLETED,
        source_address=source_addr,
        source_subaddress=source_subaddr,
        sequence=0,
    )
    assert storage.get_transaction_by_details(
        source_address=source_addr, source_subaddress=source_subaddr, sequence=0
    )


def test_wait_for_account_seq(monkeypatch: MonkeyPatch) -> None:
    account_mocker = AccountMocker()
    monkeypatch.setattr(LibraNetwork, "getAccount", account_mocker.get_account)
    seq = 2
    ar = wait_for_account_seq("addr", seq)

    assert ar.sequence == 2


def test_process_incoming_txn() -> None:
    account = create_account("fake_account")
    sender_addr = "46db232847705e05525db0336fd9f337"
    subaddr = generate_new_subaddress(account.id)

    meta = TransactionMetadata(
        metadata_type=MetadataType.GENERAL, to_subaddress=encode_subaddr(subaddr)
    )
    process_incoming_transaction(
        sender_address=sender_addr,
        receiver_address="lrw_vasp",
        sequence=1,
        amount=100,
        currency=LibraCurrency.Coin1,
        metadata=meta,
        blockchain_version=1,
    )

    # successfully parse meta and sequence
    tx = storage.get_transaction_by_details(
        source_address=sender_addr, source_subaddress=None, sequence=1
    )
    assert tx is not None


def test_balance_calculation_simple_income() -> None:
    account_id = 1
    counter_id = 0
    tx = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(account_id=account_id, transactions=[tx])

    assert balance.total == {
        LibraCurrency.LBR: 100,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }


def test_balance_calculation_two_currencies_income() -> None:
    account_id = 1
    counter_id = 0
    tx_lbr = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.COMPLETED,
    )
    tx_coin1 = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.Coin1,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[tx_lbr, tx_coin1]
    )

    assert balance.total == {
        LibraCurrency.LBR: 100,
        LibraCurrency.Coin1: 100,
        LibraCurrency.Coin2: 0,
    }


def test_balance_calculation_in_and_out() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        LibraCurrency.LBR: 50,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }


def test_balance_calculation_in_pending() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.PENDING,
    )
    balance = calc_account_balance(account_id=account_id, transactions=[income])

    assert balance.total == {
        LibraCurrency.LBR: 0,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }


def test_balance_calculation_out_pending() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.PENDING,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        LibraCurrency.LBR: 50,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }
    assert balance.frozen == {
        LibraCurrency.LBR: 50,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }


def test_balance_calculation_out_canceled() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=LibraCurrency.LBR,
        status=TransactionStatus.CANCELED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        LibraCurrency.LBR: 100,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }
    assert balance.frozen == {
        LibraCurrency.LBR: 0,
        LibraCurrency.Coin1: 0,
        LibraCurrency.Coin2: 0,
    }


def test_total_balances_calculation() -> None:
    expected = BalancesSeeder().run(db_session)
    actual = get_total_balance()

    assert expected.total == actual.total
    assert expected.frozen == actual.frozen


def send_fake_tx(amount=100, send_to_self=False) -> Tuple[int, Transaction]:
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=LibraCurrency.Coin2
    )
    account_id = user.account_id
    amount = amount
    payment_type = types.TransactionType.EXTERNAL
    currency = libra_utils.types.currencies.LibraCurrency.Coin2
    destination_addresss = "receiver_address"
    destination_subaddress = "receiver_subaddress"

    if send_to_self:
        destination_addresss = Custody().get_account_address("test_wallet")
        destination_subaddress = generate_new_subaddress(account_id)

    send_tx = send_transaction(
        sender_id=account_id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        destination_address=destination_addresss,
        destination_subaddress=destination_subaddress,
    )

    return account_id, get_transaction(send_tx.id) if send_tx else None
