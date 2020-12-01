# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context, time, pytest, typing
from offchain import offchain_business, offchain_service

from offchainapi.payment import (
    PaymentObject,
    PaymentAction,
    StatusObject,
    PaymentActor,
    Status,
)
from offchainapi.libra_address import LibraAddress

from diem import testnet

from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.services.account import generate_new_subaddress
from wallet.storage import User
from wallet.types import RegistrationStatus
from wallet.storage import db_session


CURRENCY = DiemCurrency.Coin1.value


@pytest.fixture()
def lrw1() -> offchain_business.LRW:
    return offchain_business.LRW(context.generate(1))


@pytest.fixture()
def lrw2() -> offchain_business.LRW:
    return offchain_business.LRW(context.generate(2))


@pytest.fixture()
def lrw1_onchain(lrw1: offchain_business.LRW) -> offchain_business.LRW:
    return setup_onchain_account(lrw1)


@pytest.fixture()
def lrw2_onchain(lrw2: offchain_business.LRW) -> offchain_business.LRW:
    return setup_onchain_account(lrw2)


@pytest.fixture()
def user1() -> User:
    return make_user("user1")


@pytest.fixture()
def user2() -> User:
    return make_user("user2")


@pytest.fixture()
def vasp1(
    lrw1_onchain: offchain_business.LRW,
) -> typing.Generator[typing.Any, None, None]:
    vasp = offchain_service.bootstrap(lrw1_onchain.context)
    yield vasp
    vasp.close()


@pytest.fixture()
def vasp2(
    lrw2_onchain: offchain_business.LRW,
) -> typing.Generator[typing.Any, None, None]:
    vasp = offchain_service.bootstrap(lrw2_onchain.context)
    yield vasp
    vasp.close()


@pytest.fixture()
def payment(
    lrw1: offchain_business.LRW, lrw2: offchain_business.LRW, user1, user2
) -> PaymentObject:
    user1address = generate_new_subaddress(account_id=user1.account_id)
    user2address = generate_new_subaddress(account_id=user2.account_id)

    return make_payment(
        lrw1.user_address(user1address), lrw2.user_address(user2address), 1000
    )


def setup_onchain_account(lrw: offchain_business.LRW) -> offchain_business.LRW:
    faucet = testnet.Faucet(lrw.context.jsonrpc_client)
    faucet.mint(lrw.context.auth_key().hex(), 3_000_000_000, CURRENCY)
    lrw.context.reset_dual_attestation_info()
    return lrw


def make_payment(
    sender: LibraAddress,
    receiver: LibraAddress,
    amount: int,
    currency=testnet.TEST_CURRENCY_CODE,
    action="charge",
) -> PaymentObject:
    action = PaymentAction(amount, currency, action, int(time.time()))
    status = StatusObject(Status.none)
    sender_actor = PaymentActor(sender.as_str(), status, [])
    receiver_actor = PaymentActor(receiver.as_str(), status, [])
    return PaymentObject(
        sender_actor,
        receiver_actor,
        f"{sender.get_onchain().as_str()}_abc",
        None,
        "payment description",
        action,
    )


def make_user(name: str) -> User:
    user = OneUser.run(
        db_session,
        account_amount=2000 * 1_000_000,
        account_currency=DiemCurrency.Coin1,
        registration_status=RegistrationStatus.Approved,
        account_name=f"{name}_account",
        username=name,
    )

    return user
