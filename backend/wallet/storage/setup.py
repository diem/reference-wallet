# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from wallet.storage import Base, engine


def setup_wallet_storage():
    Base.metadata.create_all(bind=engine)
