#!/usr/bin/env python3
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .events import PubSubEvent
from .transaction_progress_storage import FailedTransactionEvent
from .util import load_custom_backend


class BasePubSubClient(ABC):
    """
    Base interface for PubSubClient

    Used by daemon to enqueue new events as messages to preferred pubsub broker
    """

    @abstractmethod
    def enqueue_events(self, events: List[PubSubEvent]) -> None:
        ...

    @abstractmethod
    def enqueue_expired_transactions(
        self, events: List[FailedTransactionEvent]
    ) -> None:
        ...


class LogPubSubClient(BasePubSubClient):
    """
    Dummy implementation of BasePubSubClient interface
    Logs observed events to file
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.file_path = config["file_path"]

    def _enqueue(self, events: List[Any]) -> None:
        with open(self.file_path, "a") as log_file:
            for event in events:
                log_file.write(json.dumps(event.message) + "\n")

    def enqueue_events(self, events: List[PubSubEvent]) -> None:
        self._enqueue(events)

    def enqueue_expired_transactions(
        self, events: List[FailedTransactionEvent]
    ) -> None:
        self._enqueue(events)


def create_pubsub_client(pubsub_type: str, config: Dict[str, Any]) -> BasePubSubClient:
    pubsub_class = {"logging": LogPubSubClient}.get(pubsub_type)
    if pubsub_class is None:
        pubsub_class = load_custom_backend(pubsub_type)
    return pubsub_class(config)
