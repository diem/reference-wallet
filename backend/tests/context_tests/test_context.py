# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import asyncio
import pytest
import context

from diem import testnet, utils, diem_types, stdlib, txnmetadata


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
    assert ctx.offchain_client is not None


def test_from_env():
    ctx = context.from_env()

    assert ctx.config is not None
    assert ctx.jsonrpc_client is not None
    assert ctx.custody is not None


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

    metadata = diem_types.Metadata.bcs_deserialize(bytes.fromhex(script.metadata))
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
    metadata, sig_msg = txnmetadata.travel_rule(
        reference_id,
        sender.config.vasp_account_address(),
        amount,
    )
    metadata_signature = receiver.config.compliance_private_key().sign(sig_msg)
    txn = sender.p2p_by_travel_rule(
        receiver.config.vasp_address,
        testnet.TEST_CURRENCY_CODE,
        amount,
        metadata,
        metadata_signature,
    )

    assert txn
    assert txn.transaction.sender.lower() == sender.config.vasp_address
    script = txn.transaction.script
    assert script.receiver.lower() == receiver.config.vasp_address
    assert script.amount == amount
    assert script.metadata_signature == metadata_signature.hex()

    metadata = diem_types.Metadata.bcs_deserialize(bytes.fromhex(script.metadata))
    assert isinstance(metadata, diem_types.Metadata__TravelRuleMetadata)
    assert metadata.value.value.off_chain_reference_id == reference_id
