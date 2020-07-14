#!/usr/bin/env python3

from abc import ABC, abstractmethod
from typing import Any, Dict, Set

from .util import load_custom_backend

""


class BaseAccountSubscriptionStorage(ABC):
    """
    Abstract class for account subscription storage
    Used by pub/sub proxy to query active subscriptions
    """

    @abstractmethod
    def contains(self, address: str) -> bool:
        ...

    @abstractmethod
    def get_accounts(self) -> Set[str]:
        """
        Optional method. Only used for EventStreamStrategy
        If your setup involves a lot of subscriptions leave it unimplemented
        """


class InMemoryAccountSubscriptionStorage(BaseAccountSubscriptionStorage):
    """
    Implementation of BaseAccountSubscriptionStorage interface
    that reads list of subscribers from static config
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.accounts = set(config["accounts"])

    def contains(self, address: str) -> bool:
        return address in self.accounts

    def get_accounts(self) -> Set[str]:
        return self.accounts


def create_account_subscription_storage(
    storage_type: str, config: Dict[str, Any]
) -> BaseAccountSubscriptionStorage:
    storage_class = {"in_memory": InMemoryAccountSubscriptionStorage}.get(storage_type)
    if storage_class is None:
        storage_class = load_custom_backend(storage_type)
    return storage_class(config)
