# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

from libra_utils.custody import Custody
from libra_utils.vasp import Vasp

Custody.init()


class OnchainWallet(Vasp):
    def __init__(self):
        wallet_custody_account_name = os.getenv("WALLET_CUSTODY_ACCOUNT_NAME", "wallet")
        super().__init__(wallet_custody_account_name)
