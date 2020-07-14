#!/usr/bin/env python3

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    cast,
)

import pylibra

from .account_subscription_storage import (
    BaseAccountSubscriptionStorage,
    create_account_subscription_storage,
)
from .events import PubSubEvent
from .settings import Settings
from .util import load_custom_backend, transform_address


TProgressState = TypeVar("TProgressState", bound="ProgressState")


class ProgressState(ABC):
    @abstractmethod
    def serialize(self) -> str:
        ...

    @classmethod
    @abstractmethod
    def deserialize(cls, raw_data: str) -> ProgressState:
        ...


class AbstractStrategy(ABC, Generic[TProgressState]):
    """
    Abstract class for defining sync strategy for pub/sub daemon
    """

    def __init__(
        self,
        libra_client: pylibra.LibraNetwork,
        subscription_storage: BaseAccountSubscriptionStorage,
        config: Dict[str, Any],
    ) -> None:
        self.libra_client = libra_client
        self.subscription_storage = subscription_storage

    @abstractmethod
    def sync(self, state: TProgressState) -> Tuple[List[PubSubEvent], TProgressState]:
        ...

    @classmethod
    @abstractmethod
    def init_state(cls, raw_state: Optional[str]) -> TProgressState:
        ...


class TailBlockchainStrategyState(ProgressState):
    def __init__(self, version: int, timestamp: int) -> None:
        self.version = version
        self.timestamp = timestamp

    def serialize(self) -> str:
        info = {"version": self.version, "timestamp": self.timestamp}
        return json.dumps(info)

    @classmethod
    def deserialize(cls, raw_data: str) -> TailBlockchainStrategyState:
        data = json.loads(raw_data)
        return cls(data["version"], data["timestamp"])

    def __repr__(self) -> str:
        return f"version: {self.version}. timestamp: {self.timestamp}"


class TailBlockchainStrategy(AbstractStrategy[TailBlockchainStrategyState]):
    """
    Strategy based on tailing latest blockchain transactions and filtering relevant events
    Recommended for setups with large number of subscriptions
    """

    def __init__(
        self,
        libra_client: pylibra.LibraNetwork,
        subscription_storage: BaseAccountSubscriptionStorage,
        config: Dict[str, Any],
    ) -> None:
        super().__init__(libra_client, subscription_storage, config)
        self.batch_size = config["batch_size"]

    def sync(
        self, state: TailBlockchainStrategyState
    ) -> Tuple[List[PubSubEvent], TailBlockchainStrategyState]:
        known_version = state.version

        response = self.libra_client.transactions_by_range(
            state.version + 1, self.batch_size, True
        )
        updates = []
        for transaction, events in response:
            # TODO: change to `known_version = transaction.version()`
            # once pylibra returns this info
            known_version += 1

            if transaction is None:
                continue

            for event in events:
                if isinstance(event, pylibra.PaymentEvent):
                    address = (
                        event.sender_address
                        if event.is_sent
                        else event.receiver_address
                    )
                    if self.subscription_storage.contains(transform_address(address)):
                        updates.append(PubSubEvent(event))

        new_state = TailBlockchainStrategyState(known_version, state.timestamp)
        return (updates, new_state)

    @classmethod
    def init_state(cls, raw_state: Optional[str]) -> TailBlockchainStrategyState:
        if raw_state:
            return TailBlockchainStrategyState.deserialize(raw_state)
        else:
            return TailBlockchainStrategyState(0, 0)


class EventStreamState:
    def __init__(self, event_key: str, sequence_number: int) -> None:
        self.event_key = event_key
        self.sequence_number = sequence_number

    def serialize(self) -> Dict[str, Any]:
        return {"event_key": self.event_key, "sequence_number": self.sequence_number}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> EventStreamState:
        return cls(data["event_key"], data["sequence_number"])

    def __repr__(self) -> str:
        return f"event_key: {self.event_key}. sequence_number: {self.sequence_number}"


class EventStreamStrategyState(ProgressState):
    def __init__(self, accounts: Dict[str, List[EventStreamState]]):
        self.accounts = accounts

    def add(self, account_resource: Optional[pylibra.AccountResource]) -> None:
        if account_resource is not None:
            self.accounts[transform_address(account_resource.address)] = [
                EventStreamState(account_resource.sent_events_key.hex(), 0),
                EventStreamState(account_resource.received_events_key.hex(), 0),
            ]

    def gc_subscriptions(self, accounts: Set[str]) -> None:
        self.accounts = {
            account: data
            for (account, data) in self.accounts.items()
            if account in accounts
        }

    def iterate(self) -> Generator[EventStreamState, None, None]:
        for event_streams in self.accounts.values():
            for event_stream in event_streams:
                yield event_stream

    def serialize(self) -> str:
        data = {}
        for account, streams in self.accounts.items():
            data[account] = [stream.serialize() for stream in streams]
        return json.dumps(data)

    @classmethod
    def deserialize(cls, raw_data: str) -> "EventStreamStrategyState":
        data = json.loads(raw_data)
        accounts = {}
        for account, event_streams in data.items():
            accounts[account] = [
                EventStreamState.deserialize(stream) for stream in event_streams
            ]
        return cls(accounts)

    def __repr__(self) -> str:
        return str(self.accounts)


class EventStreamStrategy(AbstractStrategy[EventStreamStrategyState]):
    """
    Strategy based on querying exact event streams for subscriptions
    Recommended for default setup.
    Each new subscription causes extra query to full node during sync
    """

    def __init__(
        self,
        libra_client: pylibra.LibraNetwork,
        subscription_storage: BaseAccountSubscriptionStorage,
        config: Dict[str, Any],
    ) -> None:
        super().__init__(libra_client, subscription_storage, config)
        self.batch_size = config["batch_size"]
        self.subscription_fetch_interval_ms = config["subscription_fetch_interval_ms"]
        self.subscription_last_fetch_tst: float = 0

    def sync(
        self, state: EventStreamStrategyState
    ) -> Tuple[List[PubSubEvent], EventStreamStrategyState]:
        events = []
        new_state = self.refetch_subscriptions(state)
        # TODO: utilize rpc batching here
        for event_stream in new_state.iterate():
            new_events = self.libra_client.get_events(
                event_stream.event_key, event_stream.sequence_number, self.batch_size
            )
            for event in new_events:
                events.append(PubSubEvent(event, event_stream.event_key))
                # TODO: replace hacky hardcode after pylibra update
                event_stream.sequence_number = (
                    event.__dict__["_ev_dict"]["sequence_number"] + 1
                )
        return (events, new_state)

    def refetch_subscriptions(
        self, progress_state: EventStreamStrategyState
    ) -> EventStreamStrategyState:
        if (
            time.time() - self.subscription_last_fetch_tst
            > self.subscription_fetch_interval_ms / 1000
        ):
            accounts = self.subscription_storage.get_accounts()
            for address in accounts.difference(progress_state.accounts):
                # TODO: we need to utilize json-rpc batching here
                progress_state.add(self.libra_client.getAccount(address))
            progress_state.gc_subscriptions(accounts)

        return progress_state

    @classmethod
    def init_state(cls, raw_state: Optional[str]) -> EventStreamStrategyState:
        if raw_state:
            return EventStreamStrategyState.deserialize(raw_state)
        else:
            return EventStreamStrategyState({})


def create_sync_strategy(settings: Settings) -> AbstractStrategy[ProgressState]:
    libra_client = pylibra.LibraNetwork()
    libra_client._url = settings.libra_node_uri
    subscription_storage = create_account_subscription_storage(
        settings.account_subscription_storage_type,
        settings.account_subscription_storage_config,
    )
    strategy_type = settings.sync_strategy_type
    config = settings.sync_strategy_config
    strategy_class: Type[AbstractStrategy[ProgressState]] = cast(
        Type[AbstractStrategy[ProgressState]],
        {
            "tail_blockchain": TailBlockchainStrategy,
            "event_stream": EventStreamStrategy,
        }.get(strategy_type)
        or load_custom_backend(strategy_type),
    )
    return strategy_class(libra_client, subscription_storage, config)
