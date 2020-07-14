#!/usr/bin/env python3
import logging
import time

import pylibra

from .progress_storage import create_progress_storage
from .pubsub_adapter import create_pubsub_client
from .settings import Settings
from .strategy import create_sync_strategy
from .transaction_progress_storage import (
    FailedTransactionEvent,
    TransactionFailure,
    create_transaction_progress_storage,
)


class LibraPubSubProxy:
    def __init__(self, settings: Settings) -> None:
        logging.basicConfig(level=logging.DEBUG, filename=settings.log_file)

        self.libra_client = pylibra.LibraNetwork()
        self.libra_client._url = settings.libra_node_uri

        self.sync_strategy = create_sync_strategy(settings)
        self.progress_storage = create_progress_storage(
            settings.progress_storage_type, settings.progress_storage_config
        )
        self.pubsub_client = create_pubsub_client(
            settings.pubsub_type, settings.pubsub_config
        )
        self.sync_interval_ms = settings.sync_interval_ms
        self.transaction_progress_storage = create_transaction_progress_storage(
            settings.transaction_progress_storage_type,
            settings.transaction_progress_storage_config,
        )
        self.sync_state = self.sync_strategy.init_state(
            self.progress_storage.fetch_state()
        )

    def account_subscription_sync(self) -> None:
        (events, new_state) = self.sync_strategy.sync(self.sync_state)
        self.pubsub_client.enqueue_events(events)
        self.progress_storage.save_state(new_state.serialize())
        self.sync_state = new_state

    def pending_transactions_sync(self) -> None:
        blockchain_timestamp = self.libra_client.currentTimestampUsecs()
        expired_transactions = self.transaction_progress_storage.get_expired_subscriptions(
            blockchain_timestamp
        )

        # TODO: use batching here
        events = []
        for expired_txn in expired_transactions:
            transaction = self.libra_client.transaction_by_acc_seq(
                expired_txn.sender, expired_txn.sequence_number, False
            )[0]
            if transaction is None:
                events.append(
                    FailedTransactionEvent(expired_txn, TransactionFailure.EXPIRED)
                )
            # TODO: remove hacky introspection
            elif transaction._result["vm_status"] != 4001:
                events.append(
                    FailedTransactionEvent(
                        expired_txn, TransactionFailure.FAILED_EXECUTION
                    )
                )
        self.pubsub_client.enqueue_expired_transactions(events)
        self.transaction_progress_storage.gc(blockchain_timestamp)

    def start(self) -> None:
        while True:
            try:
                self.account_subscription_sync()
                self.pending_transactions_sync()
                logging.info(f"processed next chunk. New state is {self.sync_state}")
            except Exception as exc:
                logging.error(f"failed to perform sync: {exc}")
            time.sleep(self.sync_interval_ms / 1000)
