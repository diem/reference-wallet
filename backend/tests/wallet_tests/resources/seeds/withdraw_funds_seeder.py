# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple
from uuid import UUID

from tests.wallet_tests.resources.seeds import prototypes
from wallet.services import INVENTORY_ACCOUNT_NAME
from wallet.storage import Order, Account, Transaction
from wallet.types import (
    OrderStatus,
    CoverStatus,
    Direction,
    OrderType,
    TransactionType,
    TransactionStatus,
    OrderId,
)
from diem_utils.types.currencies import DiemCurrency, FiatCurrency


class WithdrawFundsSeeder:
    @staticmethod
    def run(
        db_session,
        account_amount: int,
        account_currency: DiemCurrency,
        withdraw_amount: int,
        withdraw_to_currency: FiatCurrency,
        price: int,
    ) -> Tuple[int, int, OrderId]:
        user = deepcopy(prototypes.user)
        user.account = Account(name="fake_account_seed")
        inventory_account = Account(name=INVENTORY_ACCOUNT_NAME)
        db_session.add(user)
        db_session.add(inventory_account)
        db_session.commit()

        user_income = Transaction(
            created_timestamp=datetime.now(),
            amount=account_amount,
            currency=account_currency,
            type=TransactionType.EXTERNAL,
            status=TransactionStatus.COMPLETED,
            source_address="na",
            destination_id=user.account.id,
        )
        user.account.received_transactions.append(user_income)
        order = Order(
            amount=withdraw_amount,
            direction=Direction.Sell,
            base_currency=account_currency,
            quote_currency=withdraw_to_currency,
            order_status=OrderStatus.PendingExecution,
            cover_status=CoverStatus.PendingCover,
            order_expiration=datetime.utcnow() + timedelta(minutes=10),
            exchange_amount=price,
            order_type=OrderType.Trade,
        )
        user.orders.append(order)
        db_session.add(order)
        db_session.commit()

        return inventory_account.id, user.account.id, OrderId(UUID(order.id))
