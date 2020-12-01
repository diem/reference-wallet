# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import time
import typing
import uuid
from datetime import datetime, timedelta
from typing import Optional

from diem_utils.precise_amount import Amount
from diem_utils.types.currencies import DiemCurrency, Currencies
from diem_utils.types.liquidity.currency import Currency, CurrencyPair, CurrencyPairs
from wallet import services
from wallet import storage
from wallet.services import inventory, INVENTORY_ACCOUNT_NAME
from wallet.services.fx.fx import get_rate
from wallet.services.inventory import buy_funds, INVENTORY_COVER_CURRENCY
from wallet.services.transaction import (
    internal_transaction,
    validate_balance,
)
from wallet.storage import (
    get_order,
    update_order,
    Order,
    get_account,
    get_user,
)
from wallet.types import (
    OrderStatus,
    Direction,
    CoverStatus,
    OrderId,
    TransactionType,
    BalanceError,
    ConvertResult,
    PaymentMethodAction,
    OrderType,
)

import logging

logging.getLogger(__name__)


PAYMENT_PROCESSING_DUMMY_SLEEP_TIME = 3


def process_payment_method(
    payment_method: str, amount: int, action: PaymentMethodAction
):
    """
    In real scenario charge token will be provided by the PSP.
    This is only a very simplified simulation of it...
    :param payment_method:
    :return:
    """
    if payment_method:
        return str(uuid.uuid4())
    else:
        return None


def process_order_payment(order_id, payment_method, action: PaymentMethodAction):
    order = get_order(order_id)

    time.sleep(PAYMENT_PROCESSING_DUMMY_SLEEP_TIME)
    charge_token = process_payment_method(payment_method, order.exchange_amount, action)

    if charge_token:
        update_order(
            order_id=order_id,
            charge_token=charge_token,
            order_status=OrderStatus.Charged.value,
            payment_method=payment_method,
        )
    else:
        update_order(
            order_id=order_id,
            order_status=OrderStatus.FailedCharge.value
            if action == PaymentMethodAction.Charge
            else OrderStatus.FailedCredit,
            payment_method=payment_method,
        )

    return charge_token


def create_order(
    user_id: int,
    direction: Direction,
    amount: int,
    base_currency: Currencies,
    quote_currency: Currencies,
) -> Order:
    expiration_time = datetime.utcnow() + timedelta(minutes=10)

    conversion_rate = get_rate(
        base_currency=Currency(base_currency), quote_currency=Currency(quote_currency),
    )
    request_amount = Amount().deserialize(amount)
    exchange_amount = request_amount * conversion_rate

    order_type = OrderType.Trade

    if CurrencyPair.is_diem_to_diem(
        CurrencyPair(Currency(base_currency), Currency(quote_currency))
    ):
        order_type = OrderType.DirectConvert

    return storage.create_order(
        user_id=user_id,
        amount=request_amount.serialize(),
        direction=direction,
        base_currency=base_currency.value,
        quote_currency=quote_currency.value,
        expiration_time=expiration_time,
        exchange_amount=exchange_amount.serialize(),
        order_type=order_type.value,
    )


def process_order(order_id: OrderId, payment_method: str):
    if services.run_bg_tasks():
        from ..background_tasks.background import async_execute_order

        async_execute_order.send(order_id, payment_method)
    else:
        execute_order(order_id=order_id, payment_method=payment_method)


def execute_order(order_id: OrderId, payment_method: Optional[str] = None):
    if order_expired(order_id):
        return

    order = get_order(order_id)
    if payment_method:
        process_payment_method(
            payment_method=payment_method,
            amount=order.amount,
            action=PaymentMethodAction.Charge,
        )

    if order.order_type == OrderType.Trade:
        if execute_trade(order):
            if services.run_bg_tasks():
                from ..background_tasks.background import async_cover_order

                async_cover_order.send(order_id)
            else:
                cover_order(order_id=order_id)
    else:
        execute_convert(order)


def execute_trade(order: Order):
    inventory_account_id = get_account(account_name=INVENTORY_ACCOUNT_NAME).id
    user_account_id = get_user(order.user_id).account.id
    order_id = typing.cast(OrderId, order.id)

    base_diem_currency = DiemCurrency[order.base_currency]

    if Direction[order.direction] == Direction.Buy:
        sender_id = inventory_account_id
        receiver_id = user_account_id

        if not validate_balance(sender_id, order.amount, base_diem_currency):
            buy_funds(CurrencyPairs[f"{base_diem_currency}_{INVENTORY_COVER_CURRENCY}"])
    else:
        sender_id = user_account_id
        receiver_id = inventory_account_id

    try:
        transaction = internal_transaction(
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=order.amount,
            currency=base_diem_currency,
            payment_type=TransactionType.INTERNAL,
        )
        update_order(
            order_id=order_id,
            internal_ledger_tx=transaction.id,
            order_status=OrderStatus.Executed,
        )
        return True
    except BalanceError:
        logging.exception("execute trade")
        update_order(order_id=order_id, order_status=OrderStatus.FailedExecute)
        return False


def execute_convert(order: Order) -> ConvertResult:
    inventory_account = get_account(account_name=INVENTORY_ACCOUNT_NAME).id
    user_account = get_user(order.user_id).account.id
    order_id = typing.cast(OrderId, order.id)

    from_amount = order.amount
    from_diem_currency = DiemCurrency[order.base_currency]
    to_amount = order.exchange_amount
    to_diem_currency = DiemCurrency[order.quote_currency]

    if not validate_balance(
        sender_id=user_account, amount=from_amount, currency=from_diem_currency
    ):
        return ConvertResult.InsufficientBalance

    if not validate_balance(
        sender_id=inventory_account, amount=to_amount, currency=to_diem_currency
    ):
        return ConvertResult.InsufficientInventoryBalance

    try:
        to_inventory_tx = internal_transaction(
            sender_id=user_account,
            receiver_id=inventory_account,
            amount=from_amount,
            currency=from_diem_currency,
            payment_type=TransactionType.INTERNAL,
        )
        from_inventory_tx = internal_transaction(
            sender_id=inventory_account,
            receiver_id=user_account,
            amount=to_amount,
            currency=to_diem_currency,
            payment_type=TransactionType.INTERNAL,
        )
        update_order(
            order_id=order_id,
            internal_ledger_tx=to_inventory_tx.id,
            correlated_tx=from_inventory_tx.id,
            order_status=OrderStatus.Executed,
        )
        return ConvertResult.Success
    except Exception:
        logging.exception("execute convert")
        update_order(order_id=order_id, order_status=OrderStatus.FailedExecute)
        return ConvertResult.TransferFailure


def order_expired(order_id: OrderId):
    order = get_order(order_id)

    is_expired = datetime.utcnow() > order.order_expiration

    if is_expired:
        update_order(order_id=order_id, order_status=OrderStatus.Expired)
        return True

    return False


def is_executed(order_id: OrderId):
    order = get_order(order_id)

    return OrderStatus[order.order_status] == OrderStatus.Executed


def cover_order(order_id: OrderId):
    order = get_order(order_id)

    if order.order_type == OrderType.DirectConvert.value:
        update_order(order_id=order_id, cover_status=CoverStatus.Covered)
        return

    inventory.cover_order(order)
