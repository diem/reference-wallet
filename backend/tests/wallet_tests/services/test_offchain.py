# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
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
    get_role_2,
    all_combinations,
    Combination,
)
from wallet.storage import db_session
from wallet.types import TransactionStatus

CID = "35a1b548-3170-438f-bf3a-6ca0fef85d15"

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


def print_expected_combinations(expected_combinations):
    for comb in expected_combinations:
        print(comb)


def test_role_calculation():
    actual_combinations = get_role_2()
    expected_combinations = set(all_combinations())

    for com in actual_combinations:
        expected_combinations.remove(com)

    assert len(expected_combinations) == 0, expected_combinations
    # print_expected_combinations(
    # expected_combinations
    # )


# if both mine and incoming is pending payee must be pending and payer must be pending or None
def my_method(comb):
    # in [offchain.FundPullPreApprovalStatus.pending, None]
    return (
        comb.is_payer_address_mine
        and comb.is_payee_address_mine
        and (comb.incoming_status is offchain.FundPullPreApprovalStatus.pending)
        and (
            comb.existing_status_as_payee
            is not offchain.FundPullPreApprovalStatus.pending
        )
        and (
            (
                comb.existing_status_as_payer
                is not offchain.FundPullPreApprovalStatus.pending
            )
            or comb.existing_status_as_payer is not None
        )
    )


def test_temp():
    comb = Combination(
        offchain.FundPullPreApprovalStatus.pending, True, True, None, None
    )

    answer = my_method(comb)

    assert answer
