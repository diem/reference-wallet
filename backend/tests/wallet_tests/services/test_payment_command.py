import uuid

import context
from diem import identifier
from diem.offchain import Status
from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from tests.wallet_tests.resources.seeds.payment_command_seeder import (
    PaymentCommandSeeder,
)
from wallet.services.offchain import payment_command as pc_service
from wallet.storage import db_session, TransactionStatus
from wallet import storage
from datetime import datetime

ACTION_CHARGE = "charge"
AMOUNT = 100_000
MERCHANT_NAME = "Bond & Gurki Pet Store"
OTHER_ADDRESS = "tdm1pu2unysetgf3znj76juu532rmgrkf3wg8gqqx5qqs39vnj"
MY_ADDRESS = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"
REFERENCE_ID = "2632a018-e492-4487-81f3-775d6ecfb6ef"


def test_add_payment_command():
    """
    Add payment command for outgoing 'charge' (immediately) payment.
    Check the offchain.PaymentCommand created base on add_payment_command
    call and the DB entry
    """
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    expiration = 1802010490

    pc_service.add_payment_command(
        account_id=user.account_id,
        reference_id=REFERENCE_ID,
        vasp_address=OTHER_ADDRESS,
        merchant_name=MERCHANT_NAME,
        action=ACTION_CHARGE,
        currency=DiemCurrency.XUS,
        amount=AMOUNT,
        expiration=expiration,
    )

    check_payment_command()

    model = storage.get_payment_command(REFERENCE_ID)

    sender_address, _ = identifier.decode_account(
        model.sender_address, context.get().config.diem_address_hrp()
    )

    assert model
    assert model.reference_id == REFERENCE_ID
    assert model.merchant_name == MERCHANT_NAME
    assert model.expiration == datetime.fromtimestamp(expiration)
    assert sender_address.to_hex() == context.get().config.vasp_address
    assert model.sender_status == Status.needs_kyc_data
    assert model.receiver_address == OTHER_ADDRESS
    assert model.receiver_status == Status.none
    assert model.amount == AMOUNT


def test_update_payment_command_status():
    """Update existing 'charge' payment to be 'ready_for_settlement' as payer"""
    sender_status = Status.needs_kyc_data
    receiver_status = Status.none

    PaymentCommandSeeder.run(
        db_session,
        reference_id=REFERENCE_ID,
        amount=AMOUNT,
        sender_address=MY_ADDRESS,
        sender_status=sender_status,
        receiver_address=OTHER_ADDRESS,
        receiver_status=receiver_status,
        action=ACTION_CHARGE,
        is_sender=True,
    )

    expected_my_actor_address, _ = identifier.decode_account(
        MY_ADDRESS, context.get().config.diem_address_hrp()
    )

    check_payment_command(expected_my_actor_address=expected_my_actor_address.to_hex())

    check_payment_command_model(receiver_status, sender_status)

    updated_status = Status.ready_for_settlement
    storage.update_payment_command_sender_status(REFERENCE_ID, updated_status)

    check_payment_command_model(receiver_status, updated_status)


def check_payment_command_model(receiver_status, updated_status):
    model = storage.get_payment_command(REFERENCE_ID)

    assert model
    assert model.reference_id == REFERENCE_ID
    assert model.sender_address == MY_ADDRESS
    assert model.sender_status == updated_status
    assert model.receiver_address == OTHER_ADDRESS
    assert model.receiver_status == receiver_status
    assert model.amount == AMOUNT


def check_payment_command(expected_my_actor_address=context.get().config.vasp_address):
    payment_command = pc_service.get_payment_command(REFERENCE_ID)
    my_actor_address, _ = identifier.decode_account(
        payment_command.my_actor_address, context.get().config.diem_address_hrp()
    )

    assert payment_command
    assert payment_command.reference_id() == REFERENCE_ID
    assert payment_command.opponent_address() == OTHER_ADDRESS
    assert (
        my_actor_address.to_hex() == expected_my_actor_address
    ), f"{my_actor_address.to_hex()} != {expected_my_actor_address}"
    assert payment_command.payment.action.action == ACTION_CHARGE
    assert payment_command.payment.action.amount == AMOUNT
    assert payment_command.payment.action.currency == DiemCurrency.XUS
    assert payment_command.payment.receiver.status.status == Status.none
    assert payment_command.payment.sender.status.status == Status.needs_kyc_data
