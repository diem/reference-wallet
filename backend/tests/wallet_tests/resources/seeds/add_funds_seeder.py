# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple
from uuid import UUID

from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from tests.wallet_tests.resources.seeds import prototypes
from wallet.services import INVENTORY_ACCOUNT_NAME
from wallet.storage import Account, Transaction, Order
from wallet.types import (
    TransactionType,
    TransactionStatus,
    Direction,
    OrderStatus,
    CoverStatus,
    OrderType,
    OrderId,
)


class AddFundsSeeder:
    @staticmethod
    def run(
        db_session,
        buy_amount: int,
        buy_currency: DiemCurrency,
        pay_currency: FiatCurrency,
        pay_price: int,
    ) -> Tuple[int, int, OrderId]:
        user = deepcopy(prototypes.user)
        user.account = Account(name="fake_account_seed")
        inventory_account = Account(name=INVENTORY_ACCOUNT_NAME)
        db_session.add(user)
        db_session.add(inventory_account)
        db_session.commit()

        inventory_income = Transaction(
            created_timestamp=datetime.now(),
            amount=buy_amount,
            currency=buy_currency,
            type=TransactionType.EXTERNAL,
            status=TransactionStatus.COMPLETED,
            source_address="lp",
            destination_id=inventory_account.id,
        )
        inventory_account.received_transactions.append(inventory_income)

        order = Order(
            amount=buy_amount,
            direction=Direction.Buy,
            base_currency=buy_currency,
            quote_currency=pay_currency,
            order_status=OrderStatus.PendingExecution,
            cover_status=CoverStatus.PendingCover,
            exchange_amount=pay_price,
            order_expiration=datetime.utcnow() + timedelta(minutes=10),
            order_type=OrderType.Trade,
        )

        user.orders.append(order)
        db_session.add(order)
        db_session.commit()

        return inventory_account.id, user.account.id, OrderId(UUID(order.id))


class InventoryWithoutFundsSeeder:
    @staticmethod
    def run(
        db_session,
        buy_amount: int,
        buy_currency: DiemCurrency,
        pay_currency: FiatCurrency,
        pay_price: int,
    ) -> Tuple[int, int, OrderId]:
        user = deepcopy(prototypes.user)
        user.account = Account(name="fake_account_seed")
        inventory_account = Account(name=INVENTORY_ACCOUNT_NAME)
        db_session.add(user)
        db_session.add(inventory_account)
        db_session.commit()

        order = Order(
            amount=buy_amount,
            direction=Direction.Buy,
            base_currency=buy_currency,
            quote_currency=pay_currency,
            order_status=OrderStatus.PendingExecution,
            cover_status=CoverStatus.PendingCover,
            exchange_amount=pay_price,
            order_expiration=datetime.utcnow() + timedelta(minutes=10),
            order_type=OrderType.Trade,
        )

        user.orders.append(order)
        db_session.add(order)
        db_session.commit()

        return inventory_account.id, user.account.id, OrderId(UUID(order.id))
