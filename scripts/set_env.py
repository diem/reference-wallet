# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os

import context
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import testnet

ENV_FILE_NAME = os.getenv("ENV_FILE_NAME", ".env")

GW_PORT = int(os.getenv("GW_PORT", 8080))
GW_OFFCHAIN_SERVICE_PORT = int(os.getenv("GW_OFFCHAIN_SERVICE_PORT", 8091))
VASP_BASE_URL = os.getenv("VASP_BASE_URL", "http://localhost:8091")
LIQUIDITY_SERVICE_HOST = os.getenv("LIQUIDITY_SERVICE_HOST", "liquidity")
LIQUIDITY_SERVICE_PORT = int(os.getenv("LIQUIDITY_SERVICE_PORT", 5000))


def get_private_key_hex(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()


def to_compact_json(d: dict) -> str:
    return json.dumps(d, separators=(",", ":"))


def setup_wallet(ctx):
    wallet_env_file_path = os.path.join(os.getcwd(), "backend", ENV_FILE_NAME)
    print(f"Creating {wallet_env_file_path}")

    wallet_account_name = ctx.config.wallet_custody_account_name
    wallet_private_key = get_private_key_hex(ctx.custody._get_key(wallet_account_name))
    wallet_custody_private_keys = to_compact_json({
        wallet_account_name: wallet_private_key
    })

    print("Mint to wallet account")
    faucet = testnet.Faucet(ctx.jsonrpc_client)
    faucet.mint(ctx.auth_key().hex(), 1_000_000, "Coin1")

    print("Reset wallet account dual attestation info")
    ctx.reset_dual_attestation_info()

    with open(wallet_env_file_path, "w") as dotenv:
        dotenv.write(f"GW_PORT={GW_PORT}\n")
        dotenv.write(f"GW_OFFCHAIN_SERVICE_PORT={GW_OFFCHAIN_SERVICE_PORT}\n")
        dotenv.write(f"WALLET_CUSTODY_ACCOUNT_NAME={wallet_account_name}\n")
        dotenv.write(f"CUSTODY_PRIVATE_KEYS={wallet_custody_private_keys}\n")
        dotenv.write(
            f"VASP_ADDR={ctx.config.vasp_address}\n"
        )
        dotenv.write(f"VASP_BASE_URL={ctx.config.base_url}\n")
        dotenv.write(f"VASP_COMPLIANCE_KEY={ctx.config.vasp_compliance_key}\n")
        dotenv.write(f"OFFCHAIN_SERVICE_PORT={ctx.config.offchain_service_port}\n")
        dotenv.write(f"JSON_RPC_URL={ctx.config.json_rpc_url}\n")
        dotenv.write(f"CHAIN_ID={ctx.config.chain_id}\n")
        dotenv.write(f"GAS_CURRENCY_CODE={ctx.config.gas_currency_code}\n")

        dotenv.write(f"LIQUIDITY_SERVICE_HOST={LIQUIDITY_SERVICE_HOST}\n")
        dotenv.write(f"LIQUIDITY_SERVICE_PORT={LIQUIDITY_SERVICE_PORT}\n")


def main():
    wallet_ctx = context.generate(1)
    wallet_ctx.config.base_url = VASP_BASE_URL

    setup_wallet(wallet_ctx)


if __name__ == "__main__":
    main()
