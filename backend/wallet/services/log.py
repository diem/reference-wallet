# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from wallet.storage import save_transaction_log


def add_transaction_log(transaction_id, log) -> None:
    save_transaction_log(transaction_id=transaction_id, log=log)
