# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple

import context
import diem_utils.types.currencies
import pytest
from diem import diem_types
from offchain import Status
from diem.txnmetadata import general_metadata, travel_rule, refund_metadata
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
from wallet.storage import models
from wallet.types import TransactionDirection, TransactionType, TransactionStatus
import time
from datetime import datetime


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
        currency=DiemCurrency.XUS,
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
        currency=DiemCurrency.XUS,
        metadata=diem_types.Metadata__GeneralMetadata.bcs_deserialize(meta),
        blockchain_version=1,
    )

    # successfully parse meta and sequence
    tx = storage.get_transaction_by_details(
        source_address=sender_addr, source_subaddress=None, sequence=1
    )
    assert tx is not None


def test_process_incoming_travel_rule_txn() -> None:
    account = create_account("fake_account")
    sender_address = "20ff2d6367f3f7df39d8eecc0fd50e38"
    receiver_address = "ac37b93b94ebeff3157d96d27fa1f5b6"
    sender_sub_address = "69ec5a7e45554780"
    amount = 1000 * 1_000_000
    sender = account_address(sender_address)
    sequence = 1
    currency = DiemCurrency.XUS
    blockchain_version = 1

    off_chain_reference_id = "2fec2d23-807a-4d99-84de-04a556fc0345"
    metadata, _ = travel_rule(off_chain_reference_id, sender, amount)

    storage.save_payment_command(
        models.PaymentCommand(
            my_actor_address="tdm1p4smmjwu5a0hlx9tajmf8lg04km94y8ygchn6rgqxtrysg",
            inbound=True,
            cid="a7881456-e480-4e64-b1e3-f8a9fc106c72",
            reference_id=off_chain_reference_id,
            sender_address="tdm1pyrlj6cm870ma7wwcamxql4gw8p57ckn7g4250qqctzku5",
            sender_status=Status.ready_for_settlement,
            sender_kyc_data=None,
            receiver_address="tdm1p4smmjwu5a0hlx9tajmf8lg04km94y8ygchn6rgqxtrysg",
            receiver_status=Status.ready_for_settlement,
            receiver_kyc_data=None,
            amount=amount,
            currency=currency,
            action="charge",
            created_at=datetime.fromtimestamp(int(time.time())),
            status=TransactionStatus.OFF_CHAIN_READY,
            account_id=account.id,
            recipient_signature=b"recipient_signature".hex(),
        )
    )

    process_incoming_transaction(
        sender_address=sender_address,
        receiver_address=receiver_address,
        sequence=sequence,
        amount=amount,
        currency=currency,
        metadata=diem_types.Metadata__TravelRuleMetadata.bcs_deserialize(metadata),
        blockchain_version=blockchain_version,
    )

    # successfully parse meta and sequence
    tx = storage.get_transaction_by_details(
        source_address=sender_address,
        source_subaddress=sender_sub_address,
        sequence=sequence,
    )
    assert tx is not None
    assert tx.sequence == sequence
    assert tx.blockchain_version == blockchain_version


def test_process_incoming_refund_txn() -> None:
    initial_sender_account = create_account("fake_account")
    initial_sender_subaddr = generate_new_subaddress(initial_sender_account.id)
    initial_sender_addr = "lrw_vasp"
    initial_receiver_addr = "46db232847705e05525db0336fd9f337"

    meta = refund_metadata(
        original_transaction_version=1,
        reason=diem_types.RefundReason__InvalidSubaddress(),
    )

    initial_tx = storage.add_transaction(
        amount=500,
        currency=DiemCurrency.XUS,
        payment_type=TransactionType.EXTERNAL,
        status=TransactionStatus.COMPLETED,
        source_id=initial_sender_account.id,
        source_address=initial_sender_addr,
        source_subaddress=initial_sender_subaddr,
        destination_address=initial_receiver_addr,
        blockchain_version=1,
    )

    assert initial_tx is not None
    assert initial_tx.blockchain_version == 1
    assert storage.get_transaction_by_blockchain_version(1) is not None

    process_incoming_transaction(
        sender_address=initial_receiver_addr,
        receiver_address=initial_sender_addr,
        sequence=1,
        amount=500,
        currency=DiemCurrency.XUS,
        metadata=diem_types.Metadata__RefundMetadata.bcs_deserialize(meta),
        blockchain_version=2,
    )

    tx = storage.get_transaction_by_blockchain_version(2)
    assert tx is not None
    assert tx.type == TransactionType.REFUND
    assert tx.original_txn_id == initial_tx.id


def test_balance_calculation_simple_income() -> None:
    account_id = 1
    counter_id = 0
    tx = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(account_id=account_id, transactions=[tx])

    assert balance.total == {
        DiemCurrency.XUS: 100,
    }


def test_balance_calculation_in_and_out() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.COMPLETED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.XUS: 50,
    }


def test_balance_calculation_with_locked_funds() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.LOCKED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.XUS: 50,
    }


def test_balance_calculation_in_pending() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.PENDING,
    )
    balance = calc_account_balance(account_id=account_id, transactions=[income])

    assert balance.total == {
        DiemCurrency.XUS: 0,
    }


def test_balance_calculation_out_pending() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.PENDING,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.XUS: 50,
    }
    assert balance.frozen == {
        DiemCurrency.XUS: 50,
    }


def test_balance_calculation_out_canceled() -> None:
    account_id = 1
    counter_id = 0
    income = Transaction(
        source_id=counter_id,
        destination_id=account_id,
        amount=100,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.COMPLETED,
    )
    outgoing = Transaction(
        source_id=account_id,
        destination_id=counter_id,
        amount=50,
        currency=DiemCurrency.XUS,
        status=TransactionStatus.CANCELED,
    )
    balance = calc_account_balance(
        account_id=account_id, transactions=[income, outgoing]
    )

    assert balance.total == {
        DiemCurrency.XUS: 100,
    }
    assert balance.frozen == {
        DiemCurrency.XUS: 0,
    }


def test_total_balances_calculation() -> None:
    expected = BalancesSeeder().run(db_session)
    actual = get_total_balance()

    assert expected.total == actual.total
    assert expected.frozen == actual.frozen


def send_fake_tx(amount=100, send_to_self=False) -> Tuple[int, Transaction]:
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )
    account_id = user.account_id
    amount = amount
    payment_type = types.TransactionType.EXTERNAL
    currency = diem_utils.types.currencies.DiemCurrency.XUS
    destination_address = "receiver_address"
    destination_subaddress = "receiver_subaddress"

    if send_to_self:
        destination_address = account_address_hex(context.get().config.vasp_address)
        destination_subaddress = generate_new_subaddress(account_id)

    tx_id = send_transaction(
        sender_id=account_id,
        amount=amount,
        currency=currency,
        payment_type=payment_type,
        destination_address=destination_address,
        destination_subaddress=destination_subaddress,
    )

    return account_id, get_transaction(tx_id) if tx_id else None
