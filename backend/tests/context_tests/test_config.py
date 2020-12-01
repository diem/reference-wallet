# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest, os
from context import config


def test_from_env(monkeypatch):
    def setenv(key):
        monkeypatch.setenv(key, key)

    setenv("VASP_ADDR")
    setenv("WALLET_CUSTODY_ACCOUNT_NAME")
    setenv("VASP_COMPLIANCE_KEY")
    setenv("JSON_RPC_URL")
    setenv("VASP_BASE_URL")
    setenv("GAS_CURRENCY_CODE")
    monkeypatch.setenv("CHAIN_ID", "2")
    monkeypatch.setenv("OFFCHAIN_SERVICE_PORT", "9999")

    conf = config.from_env()

    assert conf.vasp_address == "VASP_ADDR"
    assert conf.wallet_custody_account_name == "WALLET_CUSTODY_ACCOUNT_NAME"
    assert conf.vasp_compliance_key == "VASP_COMPLIANCE_KEY"
    assert conf.json_rpc_url == "JSON_RPC_URL"
    assert conf.offchain_service_port == 9999
    assert conf.base_url == "VASP_BASE_URL"
    assert conf.chain_id == 2
    assert conf.gas_currency_code == "GAS_CURRENCY_CODE"


def test_generate_config():
    account, conf = config.generate(1)

    assert conf.vasp_address == account.account_address.to_hex()
    assert conf.wallet_custody_account_name == "wallet1"
    assert (
        config.ComplianceKey.from_str(conf.vasp_compliance_key)
        == conf.offchain_compliance_key()
    )
    assert conf.compliance_public_key_bytes()
    assert conf.json_rpc_url == config.testnet.JSON_RPC_URL
    assert conf.offchain_service_port == 5091
    assert conf.base_url == "http://localhost:5091"
    assert conf.chain_id == 2
    assert conf.gas_currency_code == "Coin1"


def test_vasp_account_address():
    conf = config.from_env()
    assert conf.vasp_account_address()
    assert conf.vasp_account_address().to_hex() == conf.vasp_address


def test_vasp_diem_address():
    conf = config.from_env()
    address = conf.vasp_diem_address()
    assert address
    assert address.get_onchain_address_hex() == conf.vasp_address
    assert address.get_subaddress_hex() is None
    assert address.hrp == "tlb"


def test_diem_address_hrp():
    conf = config.from_env()
    conf.chain_id = 1
    assert conf.diem_address_hrp() == "lbr"
    conf.chain_id = 2
    assert conf.diem_address_hrp() == "tlb"
