# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from tests.wallet_tests.resources.seeds.one_user_with_one_order import (
    OneUserWithOneOrder,
)
from wallet.storage import db_session, get_order, update_order
from wallet.types import (
    OrderStatus,
    OrderId,
)


def test_get_order(clean_db: None) -> None:
    user_id, order_id = OneUserWithOneOrder().run(db_session)

    order = get_order(OrderId(UUID(order_id)))

    assert order


def test_update_order(clean_db: None) -> None:
    user_id, order_id = OneUserWithOneOrder().run(db_session)

    update_order(OrderId(UUID(order_id)), order_status=OrderStatus.FailedCredit)

    order = get_order(order_id)

    assert order.order_status == OrderStatus.FailedCredit.value
