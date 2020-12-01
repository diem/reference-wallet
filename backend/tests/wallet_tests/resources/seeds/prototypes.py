# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timedelta

from diem_utils.types.liquidity.currency import Currency
from wallet.storage import User, Order, Transaction
from wallet.types import (
    RegistrationStatus,
    Direction,
    OrderStatus,
    CoverStatus,
    OrderType,
)
from diem_utils.types.currencies import FiatCurrency

username = "test-user"

user = User(
    username=username,
    registration_status=RegistrationStatus.Approved,
    selected_fiat_currency=FiatCurrency.USD,
    selected_language="en",
    password_salt="123",
    password_hash="deadbeef",
)

order = Order(
    amount=10,
    direction=Direction.Buy.value,
    base_currency=Currency.Coin1,
    quote_currency=Currency.USD,
    order_status=OrderStatus.PendingExecution,
    cover_status=CoverStatus.PendingCover,
    payment_method="payment_method",
    exchange_amount=10,
    order_expiration=datetime.utcnow() + timedelta(minutes=10),
    order_type=OrderType.Trade,
)

tx = Transaction(
    amount=1000000,
    currency="Coin1",
    type="transfer_internal",
    status="completed",
    created_timestamp=datetime.utcnow(),
    source_id=0,
    source_address="source_address",
    source_subaddress="source_subaddress",
    destination_id=1,
    destination_address="destination_address",
    destination_subaddress="destination_subaddress",
    sequence=1,
)
