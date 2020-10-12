# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Union, Tuple, cast

import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from libra import LocalAccount
from libra.identifier import decode_account
from libra.testnet import DESIGNATED_DEALER_ADDRESS
from libra.txnmetadata import general_metadata
from libra.utils import account_address_bytes, account_address_hex
from libra.jsonrpc import Event

from libra_utils.types.currencies import LibraCurrency
from tests.wallet_tests import ASSOC_AUTHKEY
from wallet.services.transaction import process_incoming_transaction


class MockAccountResource:
    def __init__(self, address_hex: Optional[str] = None, sequence: int = 0) -> None:
        self.address: Optional[str] = address_hex
        self.sequence_number: int = sequence
        self.transactions: Dict[int, MockSignedTransaction] = {}


@dataclass
class MockSignedTransaction:
    sender: bytes
    amount: int
    currency: str
    receiver: bytes
    metadata: bytes
    sequence: Optional[int] = None
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


class BlockchainMock:
    blockchain = Blockchain()

    @classmethod
    def get_account_resource(cls, address_hex: str) -> MockAccountResource:
        if address_hex not in cls.blockchain.accounts:
            cls.blockchain.accounts[address_hex] = MockAccountResource(address_hex)

        return cls.blockchain.accounts[address_hex]


class TransactionsMocker(BlockchainMock):
    transactions: List[MockSignedTransaction] = []

    def send_transaction(
        self,
        currency: LibraCurrency,
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
            currency=LibraCurrency.Coin1,
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


class LibraNetworkMock(BlockchainMock):
    def get_account(self, address_hex: str) -> Optional[MockAccountResource]:
        return BlockchainMock.get_account_resource(address_hex)

    def transaction_by_acc_seq(
        self, addr_hex: str, seq: int, include_events: bool = False
    ) -> Tuple[
        Optional[MockSignedTransaction], List[Event],
    ]:
        account = BlockchainMock.get_account_resource(addr_hex)
        tx = account.transactions[seq]

        return tx, [Event()]

    def transactions_by_range(
        self, start_version: int, limit: int, include_events: bool = False
    ) -> List[Tuple[MockSignedTransaction, List[Event]]]:
        tx = BlockchainMock.blockchain.transactions[start_version]

        return [(tx, [Event()])]

    def sendTransaction(self, signed_transaction_bytes: bytes) -> None:
        if isinstance(signed_transaction_bytes, MockSignedTransaction):
            txn: MockSignedTransaction = cast(
                MockSignedTransaction, signed_transaction_bytes
            )

            account = BlockchainMock.get_account_resource(
                address_hex=bytes.hex(txn.sender)
            )
            account_sequence = account.sequence_number
            account.sequence_number += 1
            BlockchainMock.blockchain.version += 1

            txn_version = BlockchainMock.blockchain.version
            txn.version = txn_version
            txn.sequence = account_sequence

            TransactionsMocker.transactions.append(txn)
            BlockchainMock.blockchain.transactions[txn_version + 1] = txn
            account.transactions[account_sequence] = txn
