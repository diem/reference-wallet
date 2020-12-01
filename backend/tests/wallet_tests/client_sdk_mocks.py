# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Union, Tuple, cast

import requests
from diem.identifier import decode_account
from diem.jsonrpc import Event
from diem.testnet import DESIGNATED_DEALER_ADDRESS
from diem.txnmetadata import general_metadata
from diem.utils import account_address_bytes, account_address_hex
from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests import ASSOC_AUTHKEY
from wallet.services.transaction import process_incoming_transaction


@dataclass
class MockEventData:
    amount: int
    metadate: str
    receiver: str
    sender: str


@dataclass
class MockEventResource:
    data: MockEventData
    key: str
    sequence_number: int
    transaction_version: int


class MockedBalance:
    currency: str
    amount: int


class MockAccountResource:
    def __init__(self, address_hex: Optional[str] = None, sequence: int = 0) -> None:
        self.address: Optional[str] = address_hex
        self.sequence_number: int = sequence
        self.transactions: Dict[int, MockSignedTransaction] = {}
        self._balances: [MockedBalance] = []
        self.received_events_key: str = None
        self.sent_events_key: str = None

    @property
    def balances(self):
        return self._balances

    @balances.setter
    def balances(self, value):
        self._balances = value

    def set_received_events_key(self, received_events_key):
        self.received_events_key = received_events_key

    def set_sent_events_key(self, sent_events_key):
        self.sent_events_key = sent_events_key


@dataclass
class MockTransactionP2PScript:
    receiver: str
    amount: int
    currency: str = "Coin1"
    metadata: bytes = None
    type: str = "peer_to_peer_with_metadata"


@dataclass
class MockTransactionDetails(object):
    sequence_number: int
    sender: str
    script: MockTransactionP2PScript
    chain_id: int = 2
    type: str = "user"


@dataclass
class MockSignedTransaction:
    transaction: MockTransactionDetails
    version: Optional[int] = None


class AccountMocker:
    def __init__(self) -> None:
        self.account = MockAccountResource()

    def get_account(self, addr: str) -> MockAccountResource:
        self.account.sequence_number += 1
        return self.account


@dataclass
class Blockchain:
    version: int = 0
    transactions: Dict[int, MockSignedTransaction] = field(default_factory=lambda: {})
    accounts: Dict[str, MockAccountResource] = field(default_factory=lambda: {})
    events: Dict[str, List[MockEventResource]] = field(default_factory=lambda: {})


class BlockchainMock:
    def __init__(self):
        self.blockchain = Blockchain()

    def get_account_resource(self, address_hex: str) -> MockAccountResource:
        if address_hex not in self.blockchain.accounts:
            self.blockchain.accounts[address_hex] = MockAccountResource(address_hex)

        return self.blockchain.accounts[address_hex]


class TransactionsMocker(BlockchainMock):
    transactions: List[MockSignedTransaction] = []

    def send_transaction(
        self,
        currency: DiemCurrency,
        amount: int,
        dest_vasp_address: str,
        dest_sub_address: str,
        source_sub_address: str = None,
    ) -> Tuple[int, int]:
        return 1, 1

    def transaction_by_acc_seq(
        self, addr: str, seq: int, include_events: bool = False
    ) -> Tuple[Union[MockSignedTransaction, None], None]:
        if len(self.transactions) == 0:
            return None, None
        txn = self.transactions.pop(0)
        return txn, None


class FaucetUtilsMock(BlockchainMock):
    def mint(
        self,
        authkey_hex: str,
        amount: int,
        identifier: str,
        session: Optional[requests.Session] = None,
        timeout: Optional[Union[float, Tuple[float, float]]] = None,
    ) -> int:
        dd_address_hex = account_address_hex(DESIGNATED_DEALER_ADDRESS)
        account = BlockchainMock.get_account_resource(dd_address_hex)
        sequence = account.sequence_number
        version = BlockchainMock.blockchain.version

        decoded_addr, decoded_subaddr = decode_account(authkey_hex)

        metadata = general_metadata(to_subaddress=decoded_subaddr)

        address_hex_bytes = account_address_bytes(decoded_addr)

        process_incoming_transaction(
            sender_address=dd_address_hex,
            receiver_address=authkey_hex,
            sequence=sequence,
            amount=amount,
            currency=DiemCurrency.Coin1,
            metadata=metadata,
        )

        BlockchainMock.blockchain.version += 1

        tx = MockSignedTransaction(
            sender=bytes.fromhex(ASSOC_AUTHKEY),
            amount=amount,
            currency=identifier,
            receiver=address_hex_bytes,
            metadata=metadata,
            sequence=account.sequence_number,
            version=version,
        )
        account.sequence_number += 1
        account.transactions[sequence] = tx
        BlockchainMock.blockchain.transactions[version] = tx

        return sequence


class DiemNetworkMock(BlockchainMock):
    def add_events(self, event_stream_key: str, events):
        if event_stream_key not in self.blockchain.events:
            self.blockchain.events[event_stream_key] = []

        self.blockchain.events[event_stream_key].extend(events)

    def get_events(
        self, event_stream_key: str, start: int, limit: int
    ) -> List[MockEventResource]:
        result = []
        stop = start + limit

        if event_stream_key in self.blockchain.events:
            if len(self.blockchain.events[event_stream_key]) < start + limit:
                stop = len(self.blockchain.events[event_stream_key])

            for i in range(start, stop):
                result.append(self.blockchain.events[event_stream_key][i])

        return result

    def add_account_transactions(self, addr_hex, txs):
        account = self.get_account_resource(addr_hex)
        account.transactions = txs

        for tx in txs:
            self.blockchain.transactions[tx.version] = tx

    def get_account_transactions(self, addr_hex: str, sequence: int, limit: int):
        result = []
        stop = sequence + limit

        transactions = self.get_account_resource(addr_hex).transactions

        if len(transactions) < stop:
            stop = len(transactions)

        for i in range(sequence, stop):
            result.append(transactions[i])

        return result

    def get_account(self, address_hex: str) -> Optional[MockAccountResource]:
        return self.get_account_resource(address_hex)

    def transaction_by_acc_seq(
        self, addr_hex: str, seq: int, include_events: bool = False
    ) -> Tuple[
        Optional[MockSignedTransaction], List[Event],
    ]:
        account = self.get_account_resource(addr_hex)
        tx = account.transactions[seq]

        return tx, [Event()]

    def get_transactions(
        self, start_version: int, limit: int, include_events: bool = False
    ) -> List[MockSignedTransaction]:
        result = []

        for j in range(start_version, start_version + limit):
            tx = self.blockchain.transactions[j]
            result.append(tx)

        return result

    def sendTransaction(self, signed_transaction_bytes: bytes) -> None:
        if isinstance(signed_transaction_bytes, MockSignedTransaction):
            txn: MockSignedTransaction = cast(
                MockSignedTransaction, signed_transaction_bytes
            )

            account = self.get_account_resource(address_hex=bytes.hex(txn.sender))
            account_sequence = account.sequence_number
            account.sequence_number += 1
            self.blockchain.version += 1

            txn_version = self.blockchain.version
            txn.version = txn_version
            txn.sequence = account_sequence

            TransactionsMocker.transactions.append(txn)
            self.blockchain.transactions[txn_version + 1] = txn
            account.transactions[account_sequence] = txn
