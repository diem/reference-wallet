# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Tuple
from uuid import UUID

from diem_utils.types.liquidity.currency import Currency
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
    Balance,
)
from diem_utils.types.currencies import DiemCurrency, FiatCurrency


class BalancesSeeder:
    @staticmethod
    def run(db_session) -> Balance:
        user = deepcopy(prototypes.user)
        user.account = Account(name="fake_account_seed")
        inventory_account = Account(name=INVENTORY_ACCOUNT_NAME)
        db_session.add(user)
        db_session.add(inventory_account)
        db_session.commit()

        def credit(amount, currency, status):
            tx = deepcopy(prototypes.tx)
            tx.amount = amount
            tx.currency = currency
            tx.source_id = None
            tx.destination_id = user.account.id
            tx.type = TransactionType.EXTERNAL
            tx.status = status
            db_session.add(tx)

        def debit(amount, currency, status):
            tx = deepcopy(prototypes.tx)
            tx.amount = amount
            tx.currency = currency
            tx.source_id = user.account.id
            tx.destination_id = None
            tx.type = TransactionType.EXTERNAL
            tx.status = status
            db_session.add(tx)

        credit(1_000_000, Currency.Coin1, TransactionStatus.COMPLETED)
        credit(1_500_000, Currency.Coin1, TransactionStatus.COMPLETED)
        credit(2_000_000, Currency.Coin1, TransactionStatus.PENDING)
        credit(3_000_000, Currency.Coin1, TransactionStatus.CANCELED)
        debit(500_000, Currency.Coin1, TransactionStatus.PENDING)

        db_session.commit()

        balance = Balance()
        balance.frozen[Currency.Coin1.value] = 500_000
        balance.total[Currency.Coin1.value] = 2_000_000

        return balance
