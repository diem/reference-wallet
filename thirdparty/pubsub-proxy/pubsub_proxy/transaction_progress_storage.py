#!/usr/bin/env python3

from abc import ABC, abstractmethod
from collections import namedtuple
from enum import Enum
from typing import Any, Dict, List

from .util import load_custom_backend


class TransactionFailure(Enum):
    EXPIRED = 0
    FAILED_EXECUTION = 1


PendingTransactionSubscription = namedtuple(
    "PendingTransactionSubscription", ("sender", "sequence_number", "expiration_time")
)

FailedTransactionEvent = namedtuple(
    "FailedTransactionEvent", ("expired_subscription", "reason")
)


class BaseTransactionProgressStorage(ABC):
    """
    Abstract class for storing subscriptions for pending transactions
    """

    @abstractmethod
    def get_expired_subscriptions(
        self, blockchain_timestamp: int
    ) -> List[PendingTransactionSubscription]:
        ...

    @abstractmethod
    def gc(self, blockchain_timestamp: int) -> None:
        """
        cleans up from storage expired transactions
        """
        ...


class InMemoryTransactionProgressStorage(BaseTransactionProgressStorage):
    """
    Implementation of BaseTransactionProgressStorage interface
    that tracks pending transactions in memory
    """

    def __init__(self, _config: Dict[str, Any]) -> None:
        self.subscriptions: List[PendingTransactionSubscription] = []

    def subscribe(self, subscription: PendingTransactionSubscription) -> None:
        self.subscriptions.append(subscription)

    def get_expired_subscriptions(
        self, blockchain_timestamp: int
    ) -> List[PendingTransactionSubscription]:
        return [
            subscription
            for subscription in self.subscriptions
            if subscription.expiration_time <= blockchain_timestamp
        ]

    def gc(self, blockchain_timestamp: int) -> None:
        self.subscriptions = [
            subscription
            for subscription in self.subscriptions
            if subscription.expiration_time > blockchain_timestamp
        ]


def create_transaction_progress_storage(
    storage_type: str, config: Dict[str, Any]
) -> BaseTransactionProgressStorage:
    storage_class = {"in_memory": InMemoryTransactionProgressStorage}.get(storage_type)
    if storage_class is None:
        storage_class = load_custom_backend(storage_type)
    return storage_class(config)
