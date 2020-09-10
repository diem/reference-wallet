# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os

VASP_ADDR = os.getenv("VASP_ADDR")
JSON_RPC_URL = os.getenv("JSON_RPC_URL", "https://client.testnet.libra.org/")

DEFL_CONFIG = {
    "libra_node_uri": JSON_RPC_URL,
    "sync_interval_ms": 1000,
    "log_file": "/tmp/pubsub_log",
    "progress_storage_type": "file",
    "progress_storage_config": {"path": "/tmp/pubsub_progress"},
    "account_subscription_storage_type": "in_memory",
    "account_subscription_storage_config": {"accounts": [VASP_ADDR]},
    "transaction_progress_storage_type": "in_memory",
    "transaction_progress_storage_config": {},
    "pubsub_type": "pubsub.client.LRWPubSubClient",
    "pubsub_config": {"file_path": "/tmp/pubsub_messages"},
    "sync_strategy_type": "event_stream",
    "sync_strategy_config": {"subscription_fetch_interval_ms": 1000, "batch_size": 2,},
}
