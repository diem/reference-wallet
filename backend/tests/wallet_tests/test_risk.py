# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from wallet.services import risk


def test_risk() -> None:
    user_id = 1
    assert risk.risk_check(user_id, 1)
    assert risk.risk_check(user_id, 1000000 * 1000)
    assert not risk.risk_check(user_id, 1000000 * 1000 + 1)
