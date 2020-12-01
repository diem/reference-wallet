# pyre-strict

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os, typing, tempfile, pytest
from time import time

from pubsub import types, DEFL_CONFIG
from pubsub.client import LRWPubSubClient
from diem import testnet, utils, txnmetadata, stdlib, diem_types, identifier
from offchainapi.crypto import ComplianceKey
from cryptography.hazmat.primitives import serialization
from wallet.storage import get_transaction_id_from_reference_id


def test_init_with_default_config():
    config = DEFL_CONFIG.copy()
    assert LRWPubSubClient(config)


def test_sync():
    jsonrpc_client = testnet.create_client()
    faucet = testnet.Faucet(jsonrpc_client)

    parent_vasp = faucet.gen_account()
    account = jsonrpc_client.get_account(parent_vasp.account_address)

    processor = ProcessorStub()

    config = DEFL_CONFIG.copy()
    config["accounts"] = [account.address]
    config["processor"] = processor

    with tempfile.TemporaryDirectory() as tmpdir:
        config["progress_file_path"] = tmpdir + "/progress"

        client = LRWPubSubClient(config)
        state = client.init_progress_state()

        assert state == {account.received_events_key: 0}
        new_state = client.sync(state)

        assert state == {
            account.received_events_key: 0
        }, "state pass in should be not be changed"

        # new state seq num increased, as we found the event transfered from DD account when
        # we genreate the account.
        assert new_state == {account.received_events_key: 1}
        # new state is saved
        assert new_state == client.progress.fetch_state()
        assert len(processor.events) == 1
        assert processor.events[0].sender == utils.account_address_hex(
            testnet.DESIGNATED_DEALER_ADDRESS
        )
        assert processor.events[0].receiver == account.address

        # nothing happened, do sync once, new state should be same
        new_state2 = client.sync(new_state)
        assert new_state2 == new_state
        assert new_state2 == client.progress.fetch_state()
        assert len(processor.events) == 1

        # transfer coins to account, one new event should be fetched
        currency = account.balances[0].currency
        faucet.mint(parent_vasp.auth_key.hex(), 1_000, currency)

        new_state3 = client.sync(new_state2)
        assert new_state3 == {account.received_events_key: 2}
        assert new_state3 == client.progress.fetch_state()
        assert len(processor.events) == 2

        # when init progress state, we should get back state last synced
        reload_state = client.init_progress_state()
        assert reload_state == new_state3


def test_sync_catch_error():
    jsonrpc_client = testnet.create_client()
    faucet = testnet.Faucet(jsonrpc_client)

    parent_vasp = faucet.gen_account()
    account = jsonrpc_client.get_account(parent_vasp.account_address)

    processor = ProcessorStub(True)

    config = DEFL_CONFIG.copy()
    config["accounts"] = [account.address]
    config["processor"] = processor

    with tempfile.TemporaryDirectory() as tmpdir:
        config["progress_file_path"] = tmpdir + "/progress"

        client = LRWPubSubClient(config)

        # raise error by default
        with pytest.raises(Exception):
            client.sync({account.received_events_key: 0})
        with pytest.raises(Exception):
            client.sync({account.received_events_key: 0}, False)

        # catch error, return old state
        new_state = client.sync({account.received_events_key: 0}, True)
        assert new_state == {account.received_events_key: 0}


class ProcessorStub:
    events: typing.List[types.LRWPubSubEvent]

    def __init__(self, raise_error: typing.Optional[bool] = False) -> None:
        self.events = []
        self.raise_error = raise_error

    def send(self, event: types.LRWPubSubEvent) -> None:
        if self.raise_error:
            raise Exception("raise error by test setup")
        self.events.append(event)
