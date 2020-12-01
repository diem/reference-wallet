# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from copy import deepcopy
from . import prototypes


class OneUserWithOneOrder:
    username = prototypes.username

    @staticmethod
    def run(db_session):
        user = deepcopy(prototypes.user)
        order = deepcopy(prototypes.order)

        user.orders.append(order)

        db_session.add(order)
        db_session.add(user)

        db_session.commit()

        return user.id, order.id
