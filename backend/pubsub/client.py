# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Any, List

import sys

from pubsub_proxy.events import PubSubEvent
from pubsub_proxy.pubsub_adapter import BasePubSubClient
from pubsub_proxy.transaction_progress_storage import FailedTransactionEvent
from wallet.background_tasks.background import process_incoming_txn
from .types import LRWPubSubEvent


class LRWPubSubClient(BasePubSubClient):
    def __init__(self, *args: Any) -> None:
        print(f"Loaded LRWPubSubClient with args: {args}")
        self.vasp_addr = os.getenv("VASP_ADDR")

    def enqueue_events(self, events: List[PubSubEvent]) -> None:
        for event in events:
            try:
                lrw_event = LRWPubSubEvent.fromPubSubEvent(event)
                # HACK!!!
                if len(lrw_event.sender) > 32:
                    lrw_event.sender = lrw_event.sender[len(lrw_event.sender) - 32 :]
                if len(lrw_event.receiver) > 32:
                    lrw_event.receiver = lrw_event.receiver[
                        len(lrw_event.receiver) - 32 :
                    ]
                if lrw_event.receiver == self.vasp_addr:
                    msg = process_incoming_txn.send(lrw_event)
                    print(f"SUCCESS: sent to wallet onchain {lrw_event}")
                else:
                    print(f"got a non-incoming event. will not process {lrw_event}")
            except TypeError as e:
                print(f"ERROR: could not convert pubsub types {e}")
            except Exception as e:
                print(f"ERROR: {e}")

        sys.stdout.flush()

    def enqueue_expired_transactions(
        self, events: List[FailedTransactionEvent]
    ) -> None:
        pass
