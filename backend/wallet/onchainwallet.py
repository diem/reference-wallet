# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

from libra import testnet, jsonrpc, libra_types
from libra_utils.custody import Custody
from libra_utils.vasp import Vasp

JSON_RPC_URL = os.getenv("JSON_RPC_URL", testnet.JSON_RPC_URL)
CHAIN_ID = libra_types.ChainId(value=os.getenv("CHAIN_ID", testnet.CHAIN_ID.value))

Custody.init(CHAIN_ID)


class OnchainWallet(Vasp):
    def __init__(self):
        wallet_custody_account_name = os.getenv("WALLET_CUSTODY_ACCOUNT_NAME", "wallet")
        super().__init__(jsonrpc.Client(JSON_RPC_URL), wallet_custody_account_name)
