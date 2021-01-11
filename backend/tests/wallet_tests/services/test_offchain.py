# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import time
import uuid

import context
import dataclasses

import pytest
from diem import identifier, LocalAccount, offchain, jsonrpc
from diem.offchain import FundPullPreApprovalStatus
from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from tests.wallet_tests.resources.seeds.one_funds_pull_pre_approval import (
    OneFundsPullPreApproval,
    BILLER_ADDRESS,
)
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
    approve_funds_pull_pre_approval,
    establish_funds_pull_pre_approval,
    Role,
)
from wallet.services.transaction import (
    get_transaction_by_reference_id,
)
from wallet.storage import (
    get_account_transaction_ids,
    db_session,
    User,
    Account,
    get_funds_pull_pre_approval_command,
)
from wallet.types import TransactionStatus, RegistrationStatus

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


def test_process_inbound_payment_command(monkeypatch):
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


FUNDS_PULL_PRE_APPROVAL_ID = "5fc49fa0-5f2a-4faa-b391-ac1652c57e4d"


def test_approve_funds_pull_pre_approval_no_command_in_db():
    with pytest.raises(RuntimeError, match=r"Could not find command .*"):
        approve_funds_pull_pre_approval(
            FUNDS_PULL_PRE_APPROVAL_ID, FundPullPreApprovalStatus.valid
        )


def test_approve_funds_pull_pre_approval():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    command = get_funds_pull_pre_approval_command(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.pending

    approve_funds_pull_pre_approval(
        FUNDS_PULL_PRE_APPROVAL_ID, FundPullPreApprovalStatus.valid
    )

    command = get_funds_pull_pre_approval_command(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.valid


def test_approve_funds_pull_pre_approval_command_with_wrong_status_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.closed,
    )

    with pytest.raises(RuntimeError, match=r"Could not approve command with status .*"):
        approve_funds_pull_pre_approval(
            FUNDS_PULL_PRE_APPROVAL_ID, FundPullPreApprovalStatus.valid
        )


def test_approve_funds_pull_pre_approval_invalid_status():
    with pytest.raises(
        ValueError, match=r"Status must be 'valid' or 'rejected' and not '.*'"
    ):
        approve_funds_pull_pre_approval(
            FUNDS_PULL_PRE_APPROVAL_ID, FundPullPreApprovalStatus.closed
        )


def test_establish_funds_pull_pre_approval():
    command = get_funds_pull_pre_approval_command(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command is None

    user = generate_mock_user()

    establish_funds_pull_pre_approval(
        account_id=user.account.id,
        biller_address=BILLER_ADDRESS,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        funds_pull_pre_approval_type="consent",
        expiration_timestamp=int(time.time() + 30),
        max_cumulative_unit="week",
        max_cumulative_unit_value=1,
        max_cumulative_amount=10_000_000_000,
        max_cumulative_amount_currency=currency,
        max_transaction_amount=10_000,
        max_transaction_amount_currency=currency,
        description="test_establish_funds_pull_pre_approval_command_already_exist_in_db",
    )

    command = get_funds_pull_pre_approval_command(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command.status == FundPullPreApprovalStatus.valid
    assert command.role == Role.PAYER


def generate_mock_user():
    user = User(
        username="test_user",
        registration_status=RegistrationStatus.Approved,
        selected_fiat_currency=FiatCurrency.USD,
        selected_language="en",
        password_salt="123",
        password_hash="deadbeef",
    )
    user.account = Account(name="test_user")
    db_session.add(user)
    db_session.commit()

    return user


def test_establish_funds_pull_pre_approval_expired_expiration_timestamp():
    command = get_funds_pull_pre_approval_command(FUNDS_PULL_PRE_APPROVAL_ID)

    assert command is None

    with pytest.raises(
        ValueError,
        match="expiration timestamp must be in the future",
    ):
        establish_funds_pull_pre_approval(
            account_id=1,
            biller_address=BILLER_ADDRESS,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=int(time.time() - 30),
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=10_000_000_000,
            max_cumulative_amount_currency=currency,
            max_transaction_amount=10_000,
            max_transaction_amount_currency=currency,
            description="test_establish_funds_pull_pre_approval_command_already_exist_in_db",
        )


def test_establish_funds_pull_pre_approval_command_already_exist_in_db():
    OneFundsPullPreApproval.run(
        db_session=db_session,
        funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
        status=FundPullPreApprovalStatus.pending,
    )

    with pytest.raises(
        RuntimeError,
        match=f"Command with id {FUNDS_PULL_PRE_APPROVAL_ID} already exist in db",
    ):
        establish_funds_pull_pre_approval(
            account_id=1,
            biller_address=BILLER_ADDRESS,
            funds_pull_pre_approval_id=FUNDS_PULL_PRE_APPROVAL_ID,
            funds_pull_pre_approval_type="consent",
            expiration_timestamp=int(time.time() + 30),
            max_cumulative_unit="week",
            max_cumulative_unit_value=1,
            max_cumulative_amount=10_000_000_000,
            max_cumulative_amount_currency=currency,
            max_transaction_amount=10_000,
            max_transaction_amount_currency=currency,
            description="test_establish_funds_pull_pre_approval_command_already_exist_in_db",
        )
