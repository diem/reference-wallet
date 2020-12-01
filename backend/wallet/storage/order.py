# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Optional, Union
import uuid
from datetime import datetime
from . import db_session
from .models import User, Order
from ..types import (
    Direction,
    OrderStatus,
    CoverStatus,
    OrderType,
    OrderId,
)
from diem_utils.types.currencies import DiemCurrency, FiatCurrency


def create_order(
    user_id: int,
    amount: int,
    direction: Direction,
    base_currency: Union[DiemCurrency, FiatCurrency],
    quote_currency: Union[DiemCurrency, FiatCurrency],
    expiration_time: datetime,
    exchange_amount: int,
    order_type: OrderType,
) -> Order:
    user = User.query.get(user_id)

    order = Order(
        amount=amount,
        direction=direction,
        base_currency=base_currency,
        quote_currency=quote_currency,
        order_status=OrderStatus.PendingExecution,
        cover_status=CoverStatus.PendingCover,
        order_expiration=expiration_time,
        exchange_amount=exchange_amount,
        order_type=order_type,
    )

    user.orders.append(order)

    db_session.add(order)
    db_session.commit()

    return order


def get_order(order_id: OrderId) -> Order:
    return Order.query.get(str(order_id))


def update_order(
    order_id: OrderId,
    quote_id: Optional[str] = None,
    quote_expiration: Optional[datetime] = None,
    rate: Optional[int] = None,
    internal_ledger_tx: Optional[int] = None,
    order_status: Optional[OrderStatus] = None,
    cover_status: Optional[CoverStatus] = None,
    charge_token: Optional[str] = None,
    payment_method: Optional[str] = None,
    correlated_tx: Optional[int] = None,
):
    order = Order.query.get(str(order_id))
    values = locals()
    del values["order_id"]
    changed = False
    for key, value in values.items():
        if value:
            setattr(order, key, value)
            changed = True

    if changed:
        order.last_update = datetime.utcnow()
        db_session.commit()
