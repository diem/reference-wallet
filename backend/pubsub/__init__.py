# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

VASP_ADDR = os.getenv("VASP_ADDR")
JSON_RPC_URL = os.getenv("JSON_RPC_URL", "https://testnet.libra.org/v1")

DEFL_CONFIG = {
    "libra_node_uri": JSON_RPC_URL,
    "sync_interval_ms": 1000,
    "progress_file_path": "/tmp/pubsub_progress",
    "accounts": [VASP_ADDR],
}
