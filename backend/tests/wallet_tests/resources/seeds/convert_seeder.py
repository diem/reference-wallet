# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple

from tests.wallet_tests.resources.seeds import prototypes
from wallet.services import INVENTORY_ACCOUNT_NAME
from wallet.storage import Account, Transaction, Order
from wallet.types import (
    TransactionStatus,
    Direction,
    OrderStatus,
    CoverStatus,
    OrderType,
    TransactionType,
)
from diem_utils.types.currencies import DiemCurrency


class ConvertSeeder:
    @staticmethod
    def run(
        db_session,
        account_amount: int,
        account_currency: DiemCurrency,
        inventory_amount: int,
        inventory_currency: DiemCurrency,
        convert_from_amount: int,
        convert_to_amount: int,
    ) -> Tuple[int, int, Order]:
        user = deepcopy(prototypes.user)
        user.account = Account(name="fake_account_seed")
        inventory_account = Account(name=INVENTORY_ACCOUNT_NAME)
        db_session.add(user)
        db_session.add(inventory_account)
        db_session.commit()

        inventory_income = Transaction(
            created_timestamp=datetime.now(),
            amount=inventory_amount,
            currency=inventory_currency,
            type=TransactionType.EXTERNAL,
            status=TransactionStatus.COMPLETED,
            source_address="lp",
            destination_id=inventory_account.id,
        )
        inventory_account.received_transactions.append(inventory_income)
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
            amount=convert_from_amount,
            direction=Direction.Buy,
            base_currency=account_currency,
            quote_currency=inventory_currency,
            order_status=OrderStatus.PendingExecution,
            cover_status=CoverStatus.PendingCover,
            order_expiration=datetime.utcnow() + timedelta(minutes=10),
            exchange_amount=convert_to_amount,
            order_type=OrderType.DirectConvert,
        )
        user.orders.append(order)
        db_session.add(order)
        db_session.commit()

        return inventory_account.id, user.account.id, order
