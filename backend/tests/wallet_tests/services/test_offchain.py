# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import time
import uuid

import dataclasses

import context
from diem import identifier, LocalAccount, offchain, jsonrpc
from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet import storage
from wallet.services import offchain as offchain_service
from wallet.services.account import (
    generate_new_subaddress,
)
from wallet.services.offchain import (
    process_inbound_command,
)
from wallet.storage import db_session
from wallet.storage.funds_pull_pre_approval_command import (
    get_command as get_funds_pull_pre_approval_command,
)
from wallet.types import TransactionStatus

currency = DiemCurrency.XUS


def test_save_outbound_payment_command(monkeypatch):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    amount = 10_000_000_000
    receiver = LocalAccount.generate()
    sub_address = identifier.gen_subaddress()
    cmd = offchain_service.save_outbound_payment_command(
        user.account_id, receiver.account_address, sub_address, amount, currency
    )

    assert cmd is not None
    assert cmd.reference_id() is not None

    model = storage.get_payment_command(cmd.reference_id())
    assert model is not None
    assert model.reference_id is not None
    assert model.status == TransactionStatus.OFF_CHAIN_OUTBOUND

    with monkeypatch.context() as m:
        m.setattr(
            context.get().offchain_client,
            "send_command",
            lambda c, _: offchain.reply_request(c.cid),
        )
        offchain_service.process_offchain_tasks()

        db_session.refresh(model)
        assert model.status == TransactionStatus.OFF_CHAIN_WAIT


def test_process_inbound_payment_command(monkeypatch):
    hrp = context.get().config.diem_address_hrp()
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    amount = 10_000_000_000
    sender = LocalAccount.generate()
    sender_sub_address = identifier.gen_subaddress()
    receiver_sub_address = generate_new_subaddress(user.account_id)
    cmd = offchain.PaymentCommand.init(
        identifier.encode_account(sender.account_address, sender_sub_address, hrp),
        offchain_service._user_kyc_data(user.account_id),
        identifier.encode_account(
            context.get().config.vasp_address, receiver_sub_address, hrp
        ),
        amount,
        currency.value,
    )

    with monkeypatch.context() as m:
        client = context.get().offchain_client
        m.setattr(
            client,
            "process_inbound_request",
            lambda _, c: client.create_inbound_payment_command(c.cid, c.payment),
        )
        code, resp = offchain_service.process_inbound_command(
            cmd.payment.sender.address, cmd
        )
        assert code == 200
        assert resp

    model = storage.get_payment_command(cmd.reference_id())
    assert model
    assert model.status == TransactionStatus.OFF_CHAIN_INBOUND
    assert model.inbound, str(cmd)

    with monkeypatch.context() as m:
        m.setattr(
            context.get().offchain_client,
            "send_command",
            lambda c, _: offchain.reply_request(c.cid),
        )
        offchain_service.process_offchain_tasks()

        db_session.refresh(model)
        assert model.status == TransactionStatus.OFF_CHAIN_OUTBOUND


def test_process_inbound_funds_pull_pre_approval_command(monkeypatch):
    hrp = context.get().config.diem_address_hrp()
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    sender = LocalAccount.generate()
    sender_subaddress = identifier.gen_subaddress()
    address = identifier.encode_account(
        sender.account_address,
        sender_subaddress,
        hrp,
    )
    biller = LocalAccount.generate()
    biller_sub_address = generate_new_subaddress(user.account_id)
    biller_address = identifier.encode_account(
        biller.account_address,
        biller_sub_address,
        hrp,
    )

    funds_pull_pre_approval = offchain.FundPullPreApprovalObject(
        funds_pull_pre_approval_id=str(uuid.uuid4()),
        address=address,
        biller_address=biller_address,
        scope=offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=int(time.time()) + 30,
            max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                unit="week",
                value=1,
                max_amount=offchain.CurrencyObject(
                    amount=10_000_000_000_000, currency=currency
                ),
            ),
        ),
        status="pending",
        description="test",
    )

    cmd = offchain.FundsPullPreApprovalCommand(
        my_actor_address=address, funds_pull_pre_approval=funds_pull_pre_approval
    )

    with monkeypatch.context() as m:
        client = context.get().offchain_client
        m.setattr(
            client,
            "process_inbound_request",
            lambda _, cmd: client.create_inbound_funds_pull_pre_approval_command(
                cmd.cid, cmd.funds_pull_pre_approval
            ),
        )
        code, resp = process_inbound_command(
            cmd.funds_pull_pre_approval.biller_address, cmd
        )
        assert code == 200
        assert resp

    stored_cmd = get_funds_pull_pre_approval_command(
        cmd.funds_pull_pre_approval.funds_pull_pre_approval_id
    )
    assert stored_cmd
    assert stored_cmd.biller_address == cmd.funds_pull_pre_approval.biller_address
    assert stored_cmd.address == cmd.funds_pull_pre_approval.address
    assert stored_cmd.status == cmd.funds_pull_pre_approval.status


def test_submit_txn_when_both_ready(monkeypatch):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=currency
    )
    amount = 10_000_000_000
    receiver = LocalAccount.generate()
    sub_address = identifier.gen_subaddress()
    cmd = offchain_service.save_outbound_payment_command(
        user.account_id, receiver.account_address, sub_address, amount, currency
    )
    receiver_cmd = dataclasses.replace(
        cmd, my_actor_address=cmd.payment.receiver.address
    )
    receiver_ready_cmd = receiver_cmd.new_command(
        recipient_signature=b"recipient_signature".hex(),
        status=offchain.Status.ready_for_settlement,
        kyc_data=offchain_service._user_kyc_data(user.account_id),
    )

    model = storage.get_payment_command(cmd.reference_id())
    assert model
    assert model.status == TransactionStatus.OFF_CHAIN_OUTBOUND
    assert not model.inbound, str(model)

    with monkeypatch.context() as m:
        client = context.get().offchain_client
        m.setattr(
            client,
            "process_inbound_request",
            lambda _, c: client.create_inbound_payment_command(c.cid, c.payment),
        )
        code, resp = offchain_service.process_inbound_command(
            cmd.payment.receiver.address, receiver_ready_cmd
        )
        assert code == 200
        assert resp
    model = storage.get_payment_command(cmd.reference_id())
    assert model
    assert model.status == TransactionStatus.OFF_CHAIN_INBOUND
    assert model.inbound, str(model)

    # sync command and submit
    with monkeypatch.context() as m:
        m.setattr(
            context.get().offchain_client,
            "send_command",
            lambda c, _: offchain.reply_request(c.cid),
        )
        m.setattr(
            context.get(),
            "p2p_by_travel_rule",
            jsonrpc_txn_sample,
        )
        offchain_service.process_offchain_tasks()

    model = storage.get_payment_command(cmd.reference_id())
    assert model.status == TransactionStatus.COMPLETED, model.reference_id
    tx = storage.get_transaction_by_reference_id(model.reference_id)
    assert tx.status == TransactionStatus.COMPLETED
    assert tx.sequence == 5
    assert tx.blockchain_version == 3232


def jsonrpc_txn_sample(*args):
    return jsonrpc.Transaction(
        version=3232,
        transaction=jsonrpc.TransactionData(sequence_number=5),
        hash="3232-hash",
    )
