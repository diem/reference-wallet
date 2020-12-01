# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import asyncio
import pytest
import context

from diem import testnet, utils, diem_types, stdlib


def test_get_set():
    ctx = context.from_env()
    context.set(ctx)
    assert context.get() == ctx


def test_from_config():
    conf = context.config.from_env()
    ctx = context.from_config(conf)

    assert ctx.config == conf
    assert ctx.jsonrpc_client is not None
    assert ctx.custody is not None


def test_from_env():
    ctx = context.from_env()

    assert ctx.config is not None
    assert ctx.jsonrpc_client is not None
    assert ctx.custody is not None


def test_raise_value_error_for_no_vasp_base_url():
    ctx = context.from_env()

    account = testnet.Faucet(ctx.jsonrpc_client).gen_account()
    with pytest.raises(ValueError):
        ctx.get_vasp_base_url(account.account_address)


def test_raise_value_error_for_no_vasp_compliance_key():
    ctx = context.from_env()

    account = testnet.Faucet(ctx.jsonrpc_client).gen_account()
    with pytest.raises(ValueError):
        ctx.get_vasp_public_compliance_key(account.account_address)


async def test_get_vasp_base_url_and_compliance_key():
    ctx = context.for_local_dev()

    testnet.Faucet(ctx.jsonrpc_client).mint(
        ctx.auth_key().hex(), 1_000_000_000, ctx.config.gas_currency_code
    )

    ctx.reset_dual_attestation_info()

    address = ctx.config.vasp_account_address()
    assert ctx.get_vasp_base_url(address) == ctx.config.base_url

    key = ctx.get_vasp_public_compliance_key(address)

    sig = await ctx.config.offchain_compliance_key().sign_message("hello")
    assert sig
    payload = await key.verify_message(sig)
    assert payload == "hello"


def test_p2p_by_general():
    ctx = context.for_local_dev()

    testnet.Faucet(ctx.jsonrpc_client).mint(
        ctx.auth_key().hex(), 1_000_000_000, ctx.config.gas_currency_code
    )
    txn = ctx.p2p_by_general(
        testnet.TEST_CURRENCY_CODE,
        1000,
        receiver_vasp_address=testnet.DESIGNATED_DEALER_ADDRESS.to_hex(),
        receiver_sub_address="aaaaa28bdeb62af3",
        sender_sub_address="ccccc28bdeb62af2",
    )
    assert txn
    assert txn.transaction.sender.lower() == ctx.config.vasp_address
    script = txn.transaction.script
    assert script.receiver.lower() == testnet.DESIGNATED_DEALER_ADDRESS.to_hex()
    assert script.amount == 1000
    assert script.metadata_signature == ""

    metadata = diem_types.Metadata.lcs_deserialize(bytes.fromhex(script.metadata))
    assert isinstance(metadata, diem_types.Metadata__GeneralMetadata)
    assert metadata.value.value.from_subaddress.hex() == "ccccc28bdeb62af2"
    assert metadata.value.value.to_subaddress.hex() == "aaaaa28bdeb62af3"


def test_p2p_by_travel_rule():
    sender = context.generate(1)
    receiver = context.generate(2)
    faucet = testnet.Faucet(sender.jsonrpc_client)
    faucet.mint(sender.auth_key().hex(), 2_000_000_000, sender.config.gas_currency_code)
    faucet.mint(receiver.auth_key().hex(), 1_000, receiver.config.gas_currency_code)
    receiver.reset_dual_attestation_info()

    reference_id = "reference_id"
    amount = 1_800_000_000
    metadata_signature = receiver.config.offchain_compliance_key().sign_dual_attestation_data(
        reference_id, sender.config.vasp_account_address().to_bytes(), amount,
    )

    txn = sender.p2p_by_travel_rule(
        testnet.TEST_CURRENCY_CODE,
        amount,
        receiver.config.vasp_address,
        reference_id,
        metadata_signature,
    )

    assert txn
    assert txn.transaction.sender.lower() == sender.config.vasp_address
    script = txn.transaction.script
    assert script.receiver.lower() == receiver.config.vasp_address
    assert script.amount == amount
    assert script.metadata_signature == metadata_signature.hex()

    metadata = diem_types.Metadata.lcs_deserialize(bytes.fromhex(script.metadata))
    assert isinstance(metadata, diem_types.Metadata__TravelRuleMetadata)
    assert metadata.value.value.off_chain_reference_id == reference_id
