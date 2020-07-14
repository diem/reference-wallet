# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

""" Risk module determines if a transaction by a user can be executed. Risk check is stubbed out for LRW
with a simple amount threshold check. """

from wallet.logging import log_execution

TX_AMOUNT_THRESHOLD = 1_000_000 * 1_000


def risk_check(user_id, amount) -> bool:
    if user_id is not None and amount <= TX_AMOUNT_THRESHOLD:
        log_execution(f"Risk check passed for user {user_id} amount {amount}")
        return True

    log_execution(f"Risk check failed for user {user_id} amount {amount}")
    return False
