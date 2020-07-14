# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""
Custody module creates and signs transactions to submit on chain.
This simulate a naive custody client SDK interface that manage private keys.
"""
import json
import os
import typing
from time import time
from typing import Dict, Optional

from pylibra import (
    LibraNetwork,
    AccountKeyUtils,
    TransactionUtils,
    AccountKey,
)

from libra_utils.types.currencies import LibraCurrency


# this is hack to allow mocking of native function (TransactionUtils.createSignedP2PTransaction is considered a native one)
# we can't just monkeypatch it, so we just wrap it with a proxy local function that we can mock easily
class ProxyTransactionUtils:
    @staticmethod
    def createSignedP2PTransaction(
        sender_private_key,
        receiver,
        sender_sequence,
        amount,
        expiration_time,
        max_gas_amount,
        gas_unit_price,
        metadata,
        identifier,
        gas_identifier,
    ):
        return TransactionUtils.createSignedP2PTransaction(
            sender_private_key=sender_private_key,
            receiver=receiver,
            sender_sequence=sender_sequence,
            amount=amount,
            expiration_time=expiration_time,
            max_gas_amount=max_gas_amount,
            gas_unit_price=gas_unit_price,
            metadata=metadata,
            identifier=identifier,
            gas_identifier=gas_identifier,
        )


class Custody:
    _accounts = {}

    @classmethod
    def _read_private_keys(cls) -> Dict[str, str]:
        private_keys_json = os.getenv("CUSTODY_PRIVATE_KEYS")
        if private_keys_json:
            return json.loads(private_keys_json)
        else:
            return {}

    @classmethod
    def init(cls):
        private_keys = cls._read_private_keys()
        for name, private_key in private_keys.items():
            cls._register_account(name, private_key)

    @classmethod
    def _register_account(cls, account_name: str, private_key_hex: str):
        private_key_bytes: bytes = bytes.fromhex(typing.cast(str, private_key_hex))
        cls._accounts[account_name] = private_key_bytes

    @classmethod
    def _get_account_key(cls, account_name: str) -> AccountKey:
        return AccountKeyUtils.from_private_key(cls._accounts[account_name])

    @classmethod
    def get_account_address(cls, account_name: str):
        return cls._get_account_key(account_name).address.hex()

    @classmethod
    def get_account_auth_key(cls, account_name: str):
        return cls._get_account_key(account_name).authentication_key.hex()

    @classmethod
    def create_signed_p2p_transaction(
        cls,
        account_name: str,
        num_coins_microlibra: int,
        currency: str,
        receiver_addr: str,
        *ignore: typing.Any,
        expiration_time: Optional[int] = None,
        max_gas_amount: int = 140000,
        gas_unit_price: int = 0,
        metadata: bytes = b"",
    ) -> bytes:
        if expiration_time is None:
            expiration_time = int(time()) + 60 * 60 * 10

        private_key_bytes, sender_sequence = cls._get_key_and_sequence(account_name)

        receiver_addr_bytes = bytes.fromhex(receiver_addr)
        print(f"Creating signed p2p transaction to {receiver_addr}")
        return ProxyTransactionUtils.createSignedP2PTransaction(
            sender_private_key=private_key_bytes,
            receiver=receiver_addr_bytes,
            sender_sequence=sender_sequence,
            amount=num_coins_microlibra,
            expiration_time=expiration_time,
            max_gas_amount=max_gas_amount,
            gas_unit_price=gas_unit_price,
            metadata=metadata,
            # TODO: offchain API: The receiver side will have signed this as part of the off-chain APIs and will have sent it to the sender side
            identifier=currency,
            gas_identifier=currency,
        )

    @classmethod
    def create_add_currency_to_vasp_transaction(
        cls,
        account_name: str,
        currency: LibraCurrency,
        *ignore: typing.Any,
        expiration_time: Optional[int] = None,
        max_gas_amount: int = 140000,
        gas_unit_price: int = 0,
        gas_currency: LibraCurrency = LibraCurrency.LBR,
    ) -> bytes:
        if expiration_time is None:
            expiration_time = int(time()) + 5 * 60

        private_key_bytes, sender_sequence = cls._get_key_and_sequence(account_name)

        return TransactionUtils.createSignedAddCurrencyTransaction(
            private_key_bytes,
            sender_sequence,
            expiration_time=expiration_time,
            max_gas_amount=max_gas_amount,
            gas_unit_price=gas_unit_price,
            identifier=currency.value,
            gas_identifier=gas_currency.value,
        )

    @classmethod
    def _get_key_and_sequence(cls, account_name):
        private_key_bytes = cls._accounts[account_name]
        account_key = AccountKeyUtils.from_private_key(private_key_bytes)
        addr_hex = account_key.address.hex()
        api = LibraNetwork()
        ar = api.getAccount(addr_hex)
        if ar is None:
            raise Exception(f"Account not found: {addr_hex}")
        sender_sequence = ar.sequence
        return private_key_bytes, sender_sequence
