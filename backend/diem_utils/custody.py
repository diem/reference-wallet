# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""
Custody module creates and signs transactions to submit on chain.
This simulate a naive custody client SDK interface that manage private keys.
"""
import json
import os
import typing
import secrets

from time import time
from typing import Dict

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import LocalAccount, diem_types, testnet

_DEFAULT_ACCOUNT_NAME = "default"


class Custody:
    _accounts = {_DEFAULT_ACCOUNT_NAME: secrets.token_bytes(32)}
    chain_id: diem_types.ChainId = testnet.CHAIN_ID

    @classmethod
    def _read_private_keys(cls) -> Dict[str, str]:
        private_keys_json = os.getenv("CUSTODY_PRIVATE_KEYS")
        if private_keys_json:
            return json.loads(private_keys_json)
        else:
            return {}

    @classmethod
    def init(cls, chain_id: diem_types.ChainId):
        cls.chain_id = chain_id
        private_keys = cls._read_private_keys()
        for name, private_key in private_keys.items():
            cls._register_account(private_key_hex=private_key, account_name=name)

    @classmethod
    def _register_account(
        cls, private_key_hex: str, account_name: str = _DEFAULT_ACCOUNT_NAME
    ):
        private_key_bytes: bytes = bytes.fromhex(typing.cast(str, private_key_hex))
        cls._accounts[account_name] = private_key_bytes

    @classmethod
    def get_account(cls, account_name: str = _DEFAULT_ACCOUNT_NAME) -> LocalAccount:
        return LocalAccount(
            Ed25519PrivateKey.from_private_bytes(cls._accounts[account_name])
        )

    @classmethod
    def create_transaction(
        cls, account_name, sender_account_sequence, script, gas_currency_code="XUS"
    ) -> diem_types.SignedTransaction:
        account = cls.get_account(account_name)

        raw_tx = diem_types.RawTransaction(
            sender=account.account_address,
            sequence_number=sender_account_sequence,
            payload=diem_types.TransactionPayload__Script(script),
            max_gas_amount=1_000_000,
            gas_unit_price=0,
            gas_currency_code=gas_currency_code,
            expiration_timestamp_secs=int(time()) + 30,
            chain_id=cls.chain_id,
        )
        return account.sign(raw_tx)
