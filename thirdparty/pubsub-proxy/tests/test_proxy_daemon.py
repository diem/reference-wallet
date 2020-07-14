#!/usr/bin/env python3
import json
import unittest
from tempfile import NamedTemporaryFile
from typing import Any, List, Tuple
from unittest.mock import MagicMock, call, patch

from pubsub_proxy.proxy import LibraPubSubProxy, Settings
from pubsub_proxy.strategy import TailBlockchainStrategyState
from pubsub_proxy.transaction_progress_storage import (
    FailedTransactionEvent,
    PendingTransactionSubscription,
    TransactionFailure,
)


class TestProxyDaemon(unittest.TestCase):
    @classmethod
    def create_settings(cls) -> Tuple[Settings, List[Any]]:
        log_file = NamedTemporaryFile()
        progress_file = NamedTemporaryFile()
        settings = Settings(
            {
                "libra_node_uri": "",
                "sync_interval_ms": 0,
                "log_file": log_file.name,
                "progress_storage_type": "file",
                "progress_storage_config": {"path": progress_file.name},
                "account_subscription_storage_type": "in_memory",
                "account_subscription_storage_config": {
                    "accounts": ["5d6e820e4224b35a4bf57f402a7f824b"]
                },
                "transaction_progress_storage_type": "in_memory",
                "transaction_progress_storage_config": {},
                "pubsub_type": "logging",
                "pubsub_config": {"file_path": log_file.name},
                "sync_strategy_type": "tail_blockchain",
                "sync_strategy_config": {"batch_size": 1},
            }
        )
        return (settings, [log_file, progress_file])

    def test_progress_state_on_exceptions(self):
        "verifies that progress state is not updated unless broker message passing was successfull"
        settings, _tmp_files = self.create_settings()
        daemon = LibraPubSubProxy(settings)
        daemon.sync_strategy.sync = lambda state: (
            [],
            TailBlockchainStrategyState(state.version + 100, 0),
        )
        daemon.pubsub_client.enqueue_events = MagicMock(
            side_effect=[RuntimeError, RuntimeError, None]
        )

        with patch("time.sleep", side_effect=[None, None, RuntimeError]):
            self.assertRaises(RuntimeError, daemon.start)
        final_state = json.loads(daemon.progress_storage.fetch_state())
        self.assertEqual(final_state["version"], 100)

    def test_pending_transaction_notification_flow(self):
        settings, _tmp_files = self.create_settings()
        daemon = LibraPubSubProxy(settings)
        address = "5d6e820e4224b35a4bf57f402a7f824b"
        # manually subscribe to few transactions
        subscriptions = [
            PendingTransactionSubscription(address, 0, 10),
            PendingTransactionSubscription(address, 1, 20),
        ]
        for subscription in subscriptions:
            daemon.transaction_progress_storage.subscribe(subscription)

        # mock pylibra use inside of daemon
        daemon.account_subscription_sync = MagicMock()
        daemon.libra_client.currentTimestampUsecs = MagicMock(side_effect=[1, 11, 21])
        daemon.libra_client.transaction_by_acc_seq = MagicMock(return_value=(None, []))
        daemon.pubsub_client.enqueue_expired_transactions = MagicMock()

        # run daemon with 3 iterations
        with patch("time.sleep", side_effect=[None, None, RuntimeError]):
            self.assertRaises(RuntimeError, daemon.start)

        # verify that expiration events were enqueued
        daemon.pubsub_client.enqueue_expired_transactions.assert_has_calls(
            [
                call([]),
                call(
                    [
                        FailedTransactionEvent(
                            subscriptions[0], TransactionFailure.EXPIRED
                        )
                    ]
                ),
                call(
                    [
                        FailedTransactionEvent(
                            subscriptions[1], TransactionFailure.EXPIRED
                        )
                    ]
                ),
            ]
        )
        # verify that subscription storage is empty now
        self.assertEqual(daemon.transaction_progress_storage.subscriptions, [])
