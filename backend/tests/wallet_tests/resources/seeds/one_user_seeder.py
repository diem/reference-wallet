# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from datetime import datetime
from typing import Optional

from tests.wallet_tests.resources.seeds import prototypes
from wallet.storage import (
    Account,
    Transaction,
    User,
)
from diem_utils.types.currencies import DiemCurrency
from wallet.types import TransactionType, TransactionStatus, RegistrationStatus


class OneUser:
    @staticmethod
    def run(
        db_session,
        account_amount: Optional[int] = None,
        account_currency: Optional[DiemCurrency] = None,
        registration_status: Optional[RegistrationStatus] = RegistrationStatus.Approved,
        account_name: str = "fake_account",
        username: Optional[str] = None,
    ) -> User:
        user = deepcopy(prototypes.user)

        if username:
            user.username = username
            user.first_name = f"{username} first name"
            user.last_name = f"{username} last name"
        user.registration_status = registration_status
        user.account = Account(name=account_name)
        db_session.add(user)
        db_session.commit()

        if account_amount and account_currency:
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
            db_session.commit()

        return user
