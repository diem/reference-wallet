# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""
This module simulates a naive custody client interface that manage private keys.
"""

import json, os, typing, time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from offchainapi.crypto import jwk, ComplianceKey


class Client:
    _accounts: typing.Dict[str, Ed25519PrivateKey]

    def __init__(self) -> None:
        self._accounts = {}

    def register(
        self, account_name: str, private_key: typing.Union[Ed25519PrivateKey, str]
    ):
        if isinstance(private_key, str):
            private_key = Ed25519PrivateKey.from_private_bytes(
                bytes.fromhex(private_key)
            )

        self._accounts[account_name] = private_key

    def get_public_key(self, account_name) -> bytes:
        """get account public key bytes."""

        return (
            self._get_key(account_name)
            .public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        )

    def sign(self, account_name: str, msg: bytes) -> bytes:
        """sign the msg by account private key return signature."""

        private_key = self._get_key(account_name)
        return private_key.sign(msg)

    def compliance_key(self, account_name: str) -> ComplianceKey:
        # TODO: should not return, sign the message and return sig instead
        private_key = self._get_key(account_name)
        return ComplianceKey(jwk.JWK.from_pyca(private_key))

    def _get_key(self, account_name: str) -> Ed25519PrivateKey:
        return self._accounts[account_name]


def from_env() -> Client:
    client = Client()

    data = os.getenv("CUSTODY_PRIVATE_KEYS")
    if data:
        return from_dict(json.loads(data))

    return Client()


def from_dict(d: typing.Dict[str, str]) -> Client:
    client = Client()
    for name, key in d.items():
        client.register(name, key)

    return client
