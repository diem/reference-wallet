# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os, typing, tempfile, pytest
from time import time

from pubsub import types, DEFL_CONFIG
from pubsub.client import LRWPubSubClient
from libra import testnet, utils, txnmetadata, stdlib, libra_types, identifier
from offchainapi.crypto import ComplianceKey


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


def test_sync_travel_rule():
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

        # transfer coins to account, one new event should be fetched
        sender_vasp = faucet.gen_account()
        sender_account = jsonrpc_client.get_account(sender_vasp.account_address)
        currency = "Coin1"
        faucet.mint(sender_vasp.auth_key.hex(), 2_000 * 1_000_000, currency)
        faucet.mint(sender_vasp.auth_key.hex(), 1_000 * 1_000_000, currency)
        receiver_compliance_key = ComplianceKey.generate()
        amount = 1500 * 1_000_000

        off_chain_reference_id = "32323abc"
        metadata, _ = txnmetadata.travel_rule(
            off_chain_reference_id, sender_vasp.account_address, amount
        )
        metadata_signature = receiver_compliance_key.sign_dual_attestation_data(
            off_chain_reference_id,
            utils.account_address_bytes(sender_vasp.account_address),
            amount,
        )

        # sender constructs transaction after off chain communication
        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency),
            payee=utils.account_address(parent_vasp.account_address),
            amount=amount,
            metadata=metadata,
            metadata_signature=metadata_signature,
        )

        seq_num = jsonrpc_client.get_account_sequence(sender_vasp.account_address)
        txn = libra_types.RawTransaction(
            sender=sender_vasp.account_address,
            sequence_number=seq_num,
            payload=libra_types.TransactionPayload__Script(script),
            max_gas_amount=1_000_000,
            gas_unit_price=0,
            gas_currency_code=currency,
            expiration_timestamp_secs=int(time()) + 30,
            chain_id=testnet.CHAIN_ID,
        )

        signed_txn = sender_vasp.sign(txn)
        jsonrpc_client.submit(signed_txn)
        executed_txn = jsonrpc_client.wait_for_transaction(signed_txn)
        assert executed_txn is not None

        new_state4 = client.sync(new_state3)
        assert new_state4 == {account.received_events_key: 2}
        assert new_state4 == client.progress.fetch_state()
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
