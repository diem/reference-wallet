# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context
import dataclasses
from diem import identifier, LocalAccount, offchain, jsonrpc
from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.services.account import (
    generate_new_subaddress,
)
from wallet.services.offchain import (
    save_outbound_transaction,
    process_offchain_tasks,
    process_inbound_command,
    _txn_payment_command,
    _user_kyc_data,
)
from wallet.services.transaction import (
    get_transaction_by_reference_id,
)
from wallet.storage import (
    get_account_transaction_ids,
    db_session,
)
from wallet.types import TransactionStatus

currency = DiemCurrency.XUS


def test_save_outbound_transaction(monkeypatch):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    amount = 10_000_000_000
    receiver = LocalAccount.generate()
    subaddress = identifier.gen_subaddress()
    txn = save_outbound_transaction(
        user.account_id, receiver.account_address, subaddress, amount, currency
    )

    assert txn.id in get_account_transaction_ids(user.account_id)
    assert txn.reference_id is not None
    assert txn.command_json is not None

    with monkeypatch.context() as m:
        m.setattr(
            context.get().offchain_client,
            "send_command",
            lambda cmd, _: offchain.reply_request(cmd.cid),
        )
        process_offchain_tasks()

        db_session.refresh(txn)
        assert txn.status == TransactionStatus.OFF_CHAIN_WAIT


def test_process_inbound_command(monkeypatch):
    hrp = context.get().config.diem_address_hrp()
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    amount = 10_000_000_000
    sender = LocalAccount.generate()
    sender_subaddress = identifier.gen_subaddress()
    receiver_subaddress = generate_new_subaddress(user.account_id)
    cmd = offchain.PaymentCommand.init(
        identifier.encode_account(sender.account_address, sender_subaddress, hrp),
        _user_kyc_data(user.account_id),
        identifier.encode_account(
            context.get().config.vasp_address, receiver_subaddress, hrp
        ),
        amount,
        currency.value,
    )

    with monkeypatch.context() as m:
        client = context.get().offchain_client
        m.setattr(
            client,
            "process_inbound_request",
            lambda _, cmd: client.create_inbound_payment_command(cmd.cid, cmd.payment),
        )
        code, resp = process_inbound_command(cmd.payment.sender.address, cmd)
        assert code == 200
        assert resp

    txn = get_transaction_by_reference_id(cmd.reference_id())
    assert txn
    assert txn.status == TransactionStatus.OFF_CHAIN_INBOUND

    cmd = _txn_payment_command(txn)
    assert cmd.is_inbound(), str(cmd)

    with monkeypatch.context() as m:
        m.setattr(
            context.get().offchain_client,
            "send_command",
            lambda cmd, _: offchain.reply_request(cmd.cid),
        )
        process_offchain_tasks()

        db_session.refresh(txn)
        assert txn.status == TransactionStatus.OFF_CHAIN_OUTBOUND


def test_submit_txn_when_both_ready(monkeypatch):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    amount = 10_000_000_000
    receiver = LocalAccount.generate()
    subaddress = identifier.gen_subaddress()
    txn = save_outbound_transaction(
        user.account_id, receiver.account_address, subaddress, amount, currency
    )
    cmd = _txn_payment_command(txn)
    receiver_cmd = dataclasses.replace(
        cmd, my_actor_address=cmd.payment.receiver.address
    )
    receiver_ready_cmd = receiver_cmd.new_command(
        recipient_signature=b"recipient_signature".hex(),
        status=offchain.Status.ready_for_settlement,
        kyc_data=_user_kyc_data(user.account_id),
    )

    with monkeypatch.context() as m:
        client = context.get().offchain_client
        m.setattr(
            client,
            "process_inbound_request",
            lambda _, c: client.create_inbound_payment_command(c.cid, c.payment),
        )
        code, resp = process_inbound_command(
            cmd.payment.receiver.address, receiver_ready_cmd
        )
        assert code == 200
        assert resp
    txn = get_transaction_by_reference_id(cmd.reference_id())
    assert txn
    assert txn.status == TransactionStatus.OFF_CHAIN_INBOUND

    cmd = _txn_payment_command(txn)
    assert cmd.is_inbound(), str(cmd)

    process_offchain_tasks()
    db_session.refresh(txn)
    assert txn.status == TransactionStatus.OFF_CHAIN_READY

    # sync command and submit
    with monkeypatch.context() as m:
        m.setattr(
            context.get().offchain_client,
            "send_command",
            lambda cmd, _: offchain.reply_request(cmd.cid),
        )
        m.setattr(
            context.get(),
            "p2p_by_travel_rule",
            jsonrpc_txn_sample,
        )
        process_offchain_tasks()

    db_session.refresh(txn)
    assert txn.status == TransactionStatus.COMPLETED
    assert txn.sequence == 5
    assert txn.blockchain_version == 3232


def jsonrpc_txn_sample(*args):
    return jsonrpc.Transaction(
        version=3232,
        transaction=jsonrpc.TransactionData(sequence_number=5),
        hash="3232-hash",
    )
