#!/usr/bin/env python3

import copy
import math
import unittest
from typing import List, Tuple
from unittest.mock import MagicMock

from unittest_data_provider import data_provider
from pubsub_proxy.strategy import EventStreamStrategy


# represent event info in wallet_tests
# consists of sender index, receiver index and amount
EventData = Tuple[int, int, int]


class MockEvent:
    def __init__(
        self,
        event_key: str,
        sequence_number: int,
        sender: str,
        receiver: str,
        amount: int,
    ) -> None:
        self.event_key = event_key
        self.sequence_number = sequence_number
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

        # TODO: hack. remove after pylibra update
        self.__dict__["_ev_dict"] = {
            "transaction_version": 0,
            "sequence_number": self.sequence_number,
        }

        self._mock = MagicMock()

    def __getattr__(self, name):
        return getattr(self._mock, name)


class EventStreamTestData:
    def __init__(self, accounts: List[str], events: List[EventData]) -> None:
        self.accounts = accounts
        self.seq_index = {account: {"sent": 0, "receive": 0} for account in accounts}
        self.events = []
        for sender_idx, receiver_idx, amount in events:
            sender, receiver = accounts[sender_idx], accounts[receiver_idx]
            self.events += [
                MockEvent(
                    _sent_key(sender),
                    self.seq_index[sender]["sent"],
                    sender,
                    receiver,
                    amount,
                ),
                MockEvent(
                    _receive_key(receiver),
                    self.seq_index[receiver]["receive"],
                    sender,
                    receiver,
                    amount,
                ),
            ]
            self.seq_index[sender]["sent"] += 1
            self.seq_index[receiver]["receive"] += 1

    def get_events(
        self, event_key: str, offset: int, batch_size: int
    ) -> List[MockEvent]:
        return [
            event
            for event in self.events
            if offset <= event.sequence_number < offset + batch_size
            and event.event_key == event_key
        ]

    def num_iterations(self, batch_size: int) -> int:
        max_seq_num = max(max(info.values()) for info in self.seq_index.values())
        return math.ceil((max_seq_num + 1) / batch_size)


def _event_stream_strategy_data_provider() -> List[
    Tuple[List[str], List[EventData], int]
]:
    return [
        (
            ["5d6e820e4224b35a4bf57f402a7f824b", "69ce533446da7d6b60d1c6f5fa0d8514"],
            [(0, 1, 1), (0, 1, 2), (0, 1, 3), (0, 1, 4), (0, 1, 5)],
            2,
        )
    ]


class TestEventStreamStrategy(unittest.TestCase):
    @data_provider(_event_stream_strategy_data_provider)
    def test_e2e_flow(
        self, accounts: List[str], events: List[EventData], batch_size: int
    ) -> None:
        event_data = EventStreamTestData(accounts, events)
        libra_client = PyLibraMock(event_data)
        subscription_storage = MagicMock()
        subscription_storage.get_accounts.return_value = set(accounts)
        config = {"batch_size": batch_size, "subscription_fetch_interval_ms": 0}
        strategy = EventStreamStrategy(libra_client, subscription_storage, config)

        sync_state = strategy.init_state(None)
        all_events = []

        for _ in range(event_data.num_iterations(batch_size)):
            previous_state = copy.deepcopy(sync_state)
            new_events, sync_state = strategy.sync(sync_state)
            # verify new state contains info for all subscriptions
            self.assertEqual(set(sync_state.accounts.keys()), set(accounts))
            # verify we made progress (e.g. fetched new events)
            self.assertTrue(len(new_events) > 0)

            # for each account verify that we made progress as we expected
            for account in accounts:
                for stream in sync_state.accounts[account]:
                    if account in previous_state.accounts:
                        last_progress = [
                            s.sequence_number
                            for s in previous_state.accounts[account]
                            if s.event_key == stream.event_key
                        ][0]
                    else:
                        last_progress = 0
                    self.assertTrue(
                        last_progress
                        <= stream.sequence_number
                        <= last_progress + batch_size
                    )
                    self.assertTrue(
                        all(
                            any(
                                ev.event_key == stream.event_key
                                and ev.sequence_number == idx
                                for ev in new_events
                            )
                            for idx in range(last_progress, stream.sequence_number)
                        )
                    )
            all_events += new_events

        # check that all events are consumed
        self.assertEqual(len(all_events), len(event_data.events))


class PyLibraMock:
    def __init__(self, test_data: EventStreamTestData) -> None:
        self.test_data = test_data

    def getAccount(self, address: str) -> MagicMock:
        account = MagicMock()
        account.address = bytes.fromhex(address)
        account.sent_events_key = bytes.fromhex(_sent_key(address))
        account.received_events_key = bytes.fromhex(_receive_key(address))
        return account

    def get_events(
        self, event_key: str, offset: int, batch_size: int
    ) -> List[MockEvent]:
        return self.test_data.get_events(event_key, offset, batch_size)


def _sent_key(address: str) -> str:
    return f"00{address}"


def _receive_key(address: str) -> str:
    return f"01{address}"
