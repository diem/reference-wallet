# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
from context import stubs
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def test_from_env(monkeypatch):
    monkeypatch.delenv("CUSTODY_PRIVATE_KEYS")

    client = stubs.custody.from_env()
    assert len(client._accounts) == 0

    monkeypatch.setenv("CUSTODY_PRIVATE_KEYS", "{}")
    client = stubs.custody.from_env()
    assert len(client._accounts) == 0

    data = """{
        "wallet":"891dc353d895c2db0a2a254b72ba7a2d9a90f611bb9d82c583fb17b688dc34a7",
        "vasp_key":"891dc353d895c2db0a2a254b72ba7a2d9a90f611bb9d82c583fb17b688dc34a7"
    }"""
    monkeypatch.setenv("CUSTODY_PRIVATE_KEYS", data)
    client = stubs.custody.from_env()
    assert len(client._accounts) == 2


def test_public_key_bytes():
    client = stubs.custody.from_dict(
        {"wallet": "891dc353d895c2db0a2a254b72ba7a2d9a90f611bb9d82c583fb17b688dc34a7"}
    )

    expected_public_key = (
        "cb8971213e54a3ec213694fad20009c731a39a3d0190e1b935442c31106b9c84"
    )
    assert client.get_public_key("wallet").hex() == expected_public_key


def test_key_error_if_account_name_not_exist():
    client = stubs.custody.from_dict({})

    with pytest.raises(KeyError):
        client.get_public_key("wallet")


def test_sign():
    client = stubs.custody.from_dict(
        {"wallet": "891dc353d895c2db0a2a254b72ba7a2d9a90f611bb9d82c583fb17b688dc34a7"}
    )

    assert (
        client.sign("wallet", bytes.fromhex("aaaaaa")).hex()
        == "3cc7f2cd0b07ad34a908c37de90e0440f123b135e5a530f28b0e198c2168783bb70e220f5c2cfe61c87d260f02005c5a1805a41914d9571a96cc8d819a326f04"
    )
