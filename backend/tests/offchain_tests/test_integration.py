# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context, time
from offchain import client

from offchainapi.payment import Status

from diem_utils.types.currencies import DiemCurrency
from wallet.services.account import generate_new_subaddress
from wallet.services.transaction import send_transaction
from wallet.types import TransactionStatus
from wallet.storage import get_single_transaction


def test_send_payment_between_vasps(lrw1, lrw2, vasp1, vasp2, user1, user2):
    sender_address = lrw1.context.config.vasp_diem_address()
    receiver_address = lrw2.context.config.vasp_diem_address()
    receiver_subaddress = generate_new_subaddress(account_id=user2.account_id)

    # setup global environment as lrw1 app
    context.set(lrw1.context)
    client.set(vasp1)

    txn = send_transaction(
        sender_id=user1.account_id,
        amount=2_000_000_000,
        currency=DiemCurrency.Coin1,
        destination_address=receiver_address.get_onchain_address_hex(),
        destination_subaddress=receiver_subaddress,
    )

    assert txn
    assert txn.off_chain
    assert len(txn.off_chain) == 1
    assert txn.off_chain[0].reference_id

    reference_id = txn.off_chain[0].reference_id

    num_tries = 20
    while num_tries > 1:
        txn = get_single_transaction(txn.id)
        if txn.status == TransactionStatus.COMPLETED:
            break
        num_tries -= 1
        time.sleep(1)

    payment = vasp1.get_payment_by_ref(reference_id)
    assert payment.sender.status.as_status() == Status.ready_for_settlement
    assert payment.receiver.status.as_status() == Status.ready_for_settlement

    payment = vasp2.get_payment_by_ref(reference_id)
    assert payment.sender.status.as_status() == Status.ready_for_settlement
    assert payment.receiver.status.as_status() == Status.ready_for_settlement
