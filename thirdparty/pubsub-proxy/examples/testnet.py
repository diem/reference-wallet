#!/usr/bin/env python3

import argparse

from pubsub_proxy.proxy import LibraPubSubProxy
from pubsub_proxy.settings import Settings


def main(libra_node_uri: str, account: str) -> None:
    config = {
        "libra_node_uri": libra_node_uri,
        "sync_interval_ms": 1000,
        "log_file": "/tmp/pubsub_log",
        "progress_storage_type": "file",
        "progress_storage_config": {"path": "/tmp/pubsub_progress"},
        "account_subscription_storage_type": "in_memory",
        "account_subscription_storage_config": {"accounts": [account]},
        "transaction_progress_storage_type": "in_memory",
        "transaction_progress_storage_config": {},
        "pubsub_type": "logging",
        "pubsub_config": {"file_path": "/tmp/pubsub_messages"},
        "sync_strategy_type": "event_stream",
        "sync_strategy_config": {
            "subscription_fetch_interval_ms": 1000,
            "batch_size": 2,
        },
    }
    settings = Settings(config)
    LibraPubSubProxy(settings).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pub/sub proxy integration test")
    parser.add_argument("uri", metavar="u", type=str, help="full node URI")
    parser.add_argument("account", metavar="a", type=str, help="subscription account")

    args = parser.parse_args()
    main(args.uri, args.account)
