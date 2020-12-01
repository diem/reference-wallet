# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from diem_utils.types.liquidity.currency import CurrencyPairs
from tests.wallet_tests.resources.seeds.add_funds_seeder import (
    AddFundsSeeder,
    InventoryWithoutFundsSeeder,
)
from wallet import storage
from wallet.services import order as order_service
from wallet.storage import db_session, get_order
from wallet.types import ConvertResult, OrderId, Direction
from wallet.types import OrderStatus, CoverStatus
from .fx.test_fx import rates
from ..resources.seeds.convert_seeder import ConvertSeeder
from ..resources.seeds.one_user_seeder import OneUser
from ..resources.seeds.withdraw_funds_seeder import WithdrawFundsSeeder


def test_create_order():
    OneUser.run(db_session)
    amount = 1000000  # 1 coin (1,000,000 micros)
    order = order_service.create_order(
        user_id=1,
        direction=Direction.Buy,
        amount=amount,
        base_currency=DiemCurrency.Coin1,
        quote_currency=FiatCurrency.USD,
    )

    assert order.exchange_amount == rates[str(CurrencyPairs.Coin1_USD.value)]


def test_add_funds(patch_blockchain: None):
    buy_amount = 1000
    buy_currency = DiemCurrency.Coin1
    inventory_id, account_id, order_id = AddFundsSeeder.run(
        db_session,
        buy_amount=buy_amount,
        buy_currency=buy_currency,
        pay_currency=FiatCurrency.EUR,
        pay_price=900,
    )

    payment_method = "4580 2601 0743 7443"

    order_service.execute_order(order_id, payment_method)

    order = get_order(order_id)
    assert order.order_status == OrderStatus.Executed.value
    assert order.cover_status == CoverStatus.Covered.value

    add_funds_transaction = storage.get_transaction(order.internal_ledger_tx)
    assert add_funds_transaction
    assert add_funds_transaction.currency == buy_currency
    assert add_funds_transaction.amount == buy_amount
    assert add_funds_transaction.source_id == inventory_id
    assert add_funds_transaction.destination_id == account_id


def test_add_funds_refund_inventory(patch_blockchain: None):
    buy_amount = 1000
    buy_currency = DiemCurrency.Coin1
    inventory_id, account_id, order_id = InventoryWithoutFundsSeeder.run(
        db_session,
        buy_amount=buy_amount,
        buy_currency=buy_currency,
        pay_currency=FiatCurrency.EUR,
        pay_price=900,
    )

    payment_method = "4580 2601 0743 7443"

    order_service.execute_order(order_id, payment_method)

    order = get_order(order_id)
    assert order.order_status == OrderStatus.Executed.value
    assert order.cover_status == CoverStatus.Covered.value

    add_funds_transaction = storage.get_transaction(order.internal_ledger_tx)
    assert add_funds_transaction
    assert add_funds_transaction.currency == buy_currency
    assert add_funds_transaction.amount == buy_amount
    assert add_funds_transaction.source_id == inventory_id
    assert add_funds_transaction.destination_id == account_id


def test_convert_insufficient_user_balance():
    inventory_id, account_id, order = ConvertSeeder.run(
        db_session,
        account_amount=500,
        account_currency=DiemCurrency.Coin1,
        inventory_amount=600,
        inventory_currency=DiemCurrency.Coin1,
        convert_from_amount=700,
        convert_to_amount=500,
    )

    assert order_service.execute_convert(order) == ConvertResult.InsufficientBalance


def test_convert_insufficient_inventory_balance():
    inventory_id, account_id, order = ConvertSeeder.run(
        db_session,
        account_amount=1000,
        account_currency=DiemCurrency.Coin1,
        inventory_amount=300,
        inventory_currency=DiemCurrency.Coin1,
        convert_from_amount=1000,
        convert_to_amount=500,
    )

    assert (
        order_service.execute_convert(order)
        == ConvertResult.InsufficientInventoryBalance
    )


def test_withdraw_funds(patch_blockchain: None):
    inventory_id, account_id, order_id = WithdrawFundsSeeder.run(
        db_session,
        account_amount=1000,
        account_currency=DiemCurrency.Coin1,
        withdraw_amount=500,
        withdraw_to_currency=FiatCurrency.USD,
        price=550,
    )
    payment_method = "4580 2601 0743 7443"

    order_service.execute_order(order_id, payment_method)

    order = get_order(order_id)
    assert order.order_status == OrderStatus.Executed.value
    assert order.cover_status == CoverStatus.Covered.value

    withdraw_transaction = storage.get_transaction(order.internal_ledger_tx)
    assert withdraw_transaction
    assert withdraw_transaction.currency == DiemCurrency.Coin1
    assert withdraw_transaction.amount == 500
    assert withdraw_transaction.source_id == account_id
    assert withdraw_transaction.destination_id == inventory_id
