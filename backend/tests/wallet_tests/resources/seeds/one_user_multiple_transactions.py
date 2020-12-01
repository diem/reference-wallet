# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy

from wallet.storage import Account
from . import prototypes


class OneUserMultipleTransactions:
    tx1_currency = "Coin1"
    tx2_currency = "Coin1"
    total_txs = 2
    username = prototypes.username

    @staticmethod
    def run(db_session):
        user = deepcopy(prototypes.user)
        user.account = Account(name="fake_account_seed")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        tx1 = deepcopy(prototypes.tx)
        tx2 = deepcopy(prototypes.tx)

        tx1.source_id = user.account_id
        tx1.sequence = 1
        tx1.currency = OneUserMultipleTransactions.tx1_currency

        tx2.destination_id = user.account_id
        tx2.sequence = tx1.sequence + 1
        tx2.currency = OneUserMultipleTransactions.tx2_currency
        user.account.sent_transactions.append(tx1)
        user.account.received_transactions.append(tx2)

        db_session.add(user)
        db_session.add(tx1)
        db_session.add(tx2)

        db_session.commit()

        return tx1, tx2, user
