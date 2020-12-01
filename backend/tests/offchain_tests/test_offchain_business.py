# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

from offchainapi.business import (
    BusinessForceAbort,
    BusinessValidationFailure,
)
from offchainapi.payment import (
    StatusObject,
    KYCData,
    Status,
)

from wallet.services.account import generate_new_subaddress
from .conftest import make_payment


def test_open_channel_to(lrw1):
    assert lrw1.open_channel_to("anything")


def test_is_sender_and_is_recipient(lrw1, lrw2, payment):
    assert lrw1.is_sender(payment)
    assert not lrw2.is_sender(payment)

    assert not lrw1.is_recipient(payment)
    assert lrw2.is_recipient(payment)


async def test_check_account_existence(lrw1, lrw2, payment):
    await lrw1.check_account_existence(payment)
    await lrw2.check_account_existence(payment)


async def test_check_account_existence_sender_not_exist(lrw1, lrw2, user2):
    user1address = "cf64428bdeb62af2"
    user2address = generate_new_subaddress(account_id=user2.account_id)
    payment = make_payment(
        lrw1.user_address(user1address), lrw2.user_address(user2address), 1000
    )

    with pytest.raises(BusinessValidationFailure):
        await lrw1.check_account_existence(payment)
    await lrw2.check_account_existence(payment)


async def test_check_account_existence_receiver_not_exist(lrw1, lrw2, user1):
    user1address = generate_new_subaddress(account_id=user1.account_id)
    user2address = "cf64428bdeb62af2"
    payment = make_payment(
        lrw1.user_address(user1address), lrw2.user_address(user2address), 1000
    )

    await lrw1.check_account_existence(payment)
    with pytest.raises(BusinessValidationFailure):
        await lrw2.check_account_existence(payment)


async def test_get_and_validate_recipient_signature(lrw1, lrw2_onchain, payment):
    # receiver signs the metadata
    sig = await lrw2_onchain.get_recipient_signature(payment)

    payment.add_recipient_signature(sig)
    # sender validates
    lrw1.validate_recipient_signature(payment)


async def test_next_kyc_to_provide_for_sender(lrw1, payment):
    payment.receiver.status = StatusObject(Status.none)
    ret = await lrw1.next_kyc_to_provide(payment)
    # kyc data is required when not set
    assert ret == {Status.needs_kyc_data}

    payment.receiver.status = StatusObject(Status.needs_kyc_data)
    ret = await lrw1.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data}

    payment.receiver.status = StatusObject(Status.soft_match)
    ret = await lrw1.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data, Status.soft_match}

    payment.receiver.status = StatusObject(Status.needs_recipient_signature)
    ret = await lrw1.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data}

    payment.receiver.status = StatusObject(Status.pending_review)
    ret = await lrw1.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data}

    payment.sender.update({"kyc_data": make_kyc_data()})

    # no kyc data needs after kyc_data is set
    payment.receiver.status = StatusObject(Status.none)
    ret = await lrw1.next_kyc_to_provide(payment)
    assert ret == set()

    payment.receiver.status = StatusObject(Status.soft_match)
    ret = await lrw1.next_kyc_to_provide(payment)
    assert ret == {Status.soft_match}


async def test_next_kyc_to_provide_for_receiver(lrw2, payment):
    payment.sender.status = StatusObject(Status.none)
    ret = await lrw2.next_kyc_to_provide(payment)
    # kyc data and signature are required when not set
    assert ret == {Status.needs_kyc_data, Status.needs_recipient_signature}

    payment.sender.status = StatusObject(Status.needs_kyc_data)
    ret = await lrw2.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data, Status.needs_recipient_signature}

    payment.sender.status = StatusObject(Status.needs_recipient_signature)
    ret = await lrw2.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data, Status.needs_recipient_signature}

    payment.sender.status = StatusObject(Status.pending_review)
    ret = await lrw2.next_kyc_to_provide(payment)
    assert ret == {Status.needs_kyc_data, Status.needs_recipient_signature}

    payment.receiver.update({"kyc_data": make_kyc_data()})
    payment.update({"recipient_signature": "sig"})
    # no kyc data needs after kyc_data is set
    payment.sender.status = StatusObject(Status.none)
    ret = await lrw2.next_kyc_to_provide(payment)
    assert ret == set()

    payment.sender.status = StatusObject(Status.needs_recipient_signature)
    ret = await lrw2.next_kyc_to_provide(payment)
    # provide recipient signature again regardless whether we set it
    # in case old signature is not valid anymore, and sender requested it again
    assert ret == {Status.needs_recipient_signature}

    payment.sender.status = StatusObject(Status.pending_review)
    ret = await lrw2.next_kyc_to_provide(payment)
    assert ret == set()


async def test_next_kyc_level_to_request_for_sender(lrw1, payment):
    ret = await lrw1.next_kyc_level_to_request(payment)
    assert ret == Status.needs_kyc_data

    payment.receiver.update({"kyc_data": make_kyc_data()})
    ret = await lrw1.next_kyc_level_to_request(payment)
    assert ret == Status.needs_recipient_signature

    payment.update({"recipient_signature": "sig"})
    ret = await lrw1.next_kyc_level_to_request(payment)
    assert ret == Status.none


async def test_next_kyc_level_to_request_for_receiver(lrw2, payment):
    ret = await lrw2.next_kyc_level_to_request(payment)
    assert ret == Status.needs_kyc_data

    payment.sender.update({"kyc_data": make_kyc_data()})
    ret = await lrw2.next_kyc_level_to_request(payment)
    assert ret == Status.none


async def test_get_extended_kyc(lrw1, lrw2, payment):
    ret = await lrw1.get_extended_kyc(payment)
    assert ret.data
    assert ret.data["payload_type"] == "KYC_DATA"
    assert ret.data["given_name"] == "user1 first name"
    assert ret.data["surname"] == "user1 last name"

    ret = await lrw2.get_extended_kyc(payment)
    assert ret.data
    assert ret.data["payload_type"] == "KYC_DATA"
    assert ret.data["given_name"] == "user2 first name"
    assert ret.data["surname"] == "user2 last name"


async def test_get_extended_kyc_unknown_user_subaddress(lrw1, lrw2, user2):
    user1address = "cf64428bdeb62af2"
    user2address = generate_new_subaddress(account_id=user2.account_id)
    payment = make_payment(
        lrw1.user_address(user1address), lrw2.user_address(user2address), 1000
    )

    with pytest.raises(BusinessForceAbort):
        await lrw1.get_extended_kyc(payment)
    assert await lrw2.get_extended_kyc(payment)


async def test_get_additional_kyc(lrw1, lrw2, payment):
    ret = await lrw1.get_additional_kyc(payment)
    assert ret.data
    assert ret.data["payload_type"] == "KYC_DATA"
    assert ret.data["given_name"] == "user1 first name"
    assert ret.data["surname"] == "user1 last name"

    ret = await lrw2.get_extended_kyc(payment)
    assert ret.data
    assert ret.data["payload_type"] == "KYC_DATA"
    assert ret.data["given_name"] == "user2 first name"
    assert ret.data["surname"] == "user2 last name"


# TODO: missing unit tests for payment_pre_processing and ready_for_settlement


def make_kyc_data():
    return KYCData(
        {"payload_type": "KYC_DATA", "payload_version": 1, "type": "individual",}
    )
