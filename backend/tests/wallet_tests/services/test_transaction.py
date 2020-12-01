# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple

import context
import diem_utils.types.currencies
import pytest
from diem import diem_types
from diem.txnmetadata import general_metadata, travel_rule
from diem.utils import sub_address, account_address_hex, account_address
from diem_utils.types.currencies import DiemCurrency

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
        currency=DiemCurrency.Coin1,
        payment_type=TransactionType.INTERNAL,
        status=TransactionStatus.COMPLETED,
        source_address=source_addr,
        source_subaddress=source_subaddr,
        sequence=0,
    )
    assert storage.get_transaction_by_details(
        source_address=source_addr, source_subaddress=source_subaddr, sequence=0
    )


def test_process_incoming_general_txn() -> None:
    account = create_account("fake_account")
    sender_addr = "46db232847705e05525db0336fd9f337"
    subaddr = generate_new_subaddress(account.id)

    meta = general_metadata(to_subaddress=sub_address(subaddr))
    process_incoming_transaction(
        sender_address=sender_addr,
        receiver_address="lrw_vasp",
        sequence=1,
        amount=100,
        currency=DiemCurrency.Coin1,
        metadata=diem_types.Metadata__GeneralMetadata.lcs_deserialize(meta),
        blockchain_version=1,
    )

    # successfully parse meta and sequence
    tx = storage.get_transaction_by_details(
        source_address=sender_addr, source_subaddress=None, sequence=1
    )
    assert tx is not None


def test_process_incoming_travel_rule_txn() -> None:
    account = create_account("fake_account")
    sender_addr = "46db232847705e05525db0336fd9f337"
    receiver_addr = "lrw_vasp"
    sender_subaddr = generate_new_subaddress(account.id)
    amount = 1000 * 1_000_000
    sender = account_address(sender_addr)
    sequence = 1
    currency = DiemCurrency.Coin1
    blockchain_version = 1

    off_chain_reference_id = "32323abc"
    metadata, _ = travel_rule(off_chain_reference_id, sender, amount)

    storage.add_transaction(
        amount=amount,
        currency=currency,
        payment_type=TransactionType.OFFCHAIN,
        status=TransactionStatus.READY_FOR_ON_CHAIN,
        source_id=account.id,
        source_address=sender_addr,
        source_subaddress=sender_subaddr,
        destination_address=receiver_addr,
        reference_id=off_chain_reference_id,
    )

    process_incoming_transaction(
        sender_address=sender_addr,
        receiver_address=receiver_addr,
        sequence=sequence,
        amount=amount,
        currency=currency,
        metadata=diem_types.Metadata__TravelRuleMetadata.lcs_deserialize(metadata),
        blockchain_version=blockchain_version,
    )

    # successfully parse meta and sequence
    tx = storage.get_transaction_by_details(
        source_address=sender_addr, source_subaddress=sender_subaddr, sequence=sequence
    )
    assert tx is not None
    assert tx.sequence == sequence
    assert tx.blockchain_version == blockchain_version


def test_balance_calculation_simple_income() -> None:
    account_id = 1
    counter_id = 0
    tx = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(account_id=account_id, transactions=[tx])

    assert balance.total == {
        DiemCurrency.Coin1: 100,
    }


def test_balance_calculation_in_and_out() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.Coin1: 50,
    }


def test_balance_calculation_in_pending() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.PENDING,
    )
    balance = calc_account_balance(account_id=account_id, transactions=[income])

    assert balance.total == {
        DiemCurrency.Coin1: 0,
    }


def test_balance_calculation_out_pending() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.PENDING,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.Coin1: 50,
    }
    assert balance.frozen == {
        DiemCurrency.Coin1: 50,
    }


def test_balance_calculation_out_canceled() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.Coin1,
        status=TransactionStatus.CANCELED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.Coin1: 100,
    }
    assert balance.frozen == {
        DiemCurrency.Coin1: 0,
    }


def test_total_balances_calculation() -> None:
    expected = BalancesSeeder().run(db_session)
    actual = get_total_balance()

    assert expected.total == actual.total
    assert expected.frozen == actual.frozen


def send_fake_tx(amount=100, send_to_self=False) -> Tuple[int, Transaction]:
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.Coin1
    )
    account_id = user.account_id
    amount = amount
    payment_type = types.TransactionType.EXTERNAL
    currency = diem_utils.types.currencies.DiemCurrency.Coin1
    destination_address = "receiver_address"
    destination_subaddress = "receiver_subaddress"

    if send_to_self:
        destination_address = account_address_hex(context.get().config.vasp_address)
        destination_subaddress = generate_new_subaddress(account_id)

    send_tx = send_transaction(
        sender_id=account_id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        destination_address=destination_address,
        destination_subaddress=destination_subaddress,
    )

    return account_id, get_transaction(send_tx.id) if send_tx else None
