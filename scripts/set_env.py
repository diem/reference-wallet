# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
from secrets import token_bytes

import sys
from pylibra import AccountKeyUtils
from offchainapi.crypto import ComplianceKey

from libra_utils.custody import Custody
from libra_utils.libra import get_network_supported_currencies, mint_and_wait
from libra_utils.vasp import Vasp


def init_onchain_account(custody_private_keys, account_name, private_key_hex):
    account_addr = public_libra_address_from_key_hex(private_key_hex)
    print(f'Creating and initialize blockchain account {account_name} @ {account_addr}')
    os.environ["CUSTODY_PRIVATE_KEYS"] = custody_private_keys
    Custody.init()
    vasp = Vasp(account_name)
    vasp.setup_blockchain()

    return vasp


if len(sys.argv) > 2 or len(sys.argv) > 1 and '--help' in sys.argv:
    print("""
    Setup wallet and liquidity environment including blockchain private keys generation.
    Usage: set_env.py
    Flags: --force      Will regenerate blockchain keys and run current .env configuration.
    """)

    exit()

GW_PORT = os.getenv("GW_PORT", 8080)
ENV_FILE_NAME = os.getenv("ENV_FILE_NAME", ".env")
LIQUIDITY_SERVICE_HOST = os.getenv("LIQUIDITY_SERVICE_HOST", "liquidity")
LIQUIDITY_SERVICE_PORT = os.getenv("LIQUIDITY_SERVICE_PORT", 5000)
OFFCHAIN_SERVICE_PORT: int = int(os.getenv("OFFCHAIN_SERVICE_PORT", 8091))
NETWORK = os.getenv("NETWORK", "testnet")
JSON_RPC_URL = os.getenv("JSON_RPC_URL", "https://testnet.libra.org/v1")
FAUCET_URL = os.getenv("FAUCET_URL", "http://testnet.libra.org/mint")
CHAIN_ID = os.getenv("CHAIN_ID", 2)

wallet_private_key_hex: str = token_bytes(32).hex()
lp_private_key_hex: str = token_bytes(32).hex()

execution_dir_path = os.getcwd()


def public_libra_address_from_key_hex(private_key_hex):
    private_key_bytes: bytes = bytes.fromhex(private_key_hex)
    return AccountKeyUtils.from_private_key(private_key_bytes).address.hex()


wallet_env_file_path = os.path.join(execution_dir_path, "backend", ENV_FILE_NAME)
liquidity_env_file_path = os.path.join(execution_dir_path, "liquidity", ENV_FILE_NAME)

if os.path.exists(wallet_env_file_path) and os.path.exists(liquidity_env_file_path):
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] != '--force'):
        print(f".env variable files are already set.\n run {sys.argv[0]} --force to recreate them")
        exit(0)

print(f"creating {wallet_env_file_path}")

# setup wallet
with open(wallet_env_file_path, "w") as dotenv:
    wallet_account_name = "wallet"
    private_keys = {f"{wallet_account_name}": wallet_private_key_hex}
    wallet_custody_private_keys = json.dumps(private_keys, separators=(',', ':'))
    dotenv.write(f"GW_PORT={GW_PORT}\n")
    dotenv.write(f"WALLET_CUSTODY_ACCOUNT_NAME={wallet_account_name}\n")
    dotenv.write(
        f"CUSTODY_PRIVATE_KEYS={wallet_custody_private_keys}\n"
    )
    dotenv.write(
        f"VASP_ADDR={public_libra_address_from_key_hex(wallet_private_key_hex)}\n"
    )
    dotenv.write(
        f"VASP_COMPLIANCE_KEY={ComplianceKey.generate().export_full()}\n"
    )
    dotenv.write(f"LIQUIDITY_SERVICE_HOST={LIQUIDITY_SERVICE_HOST}\n")
    dotenv.write(f"LIQUIDITY_SERVICE_PORT={LIQUIDITY_SERVICE_PORT}\n")
    dotenv.write(f"OFFCHAIN_SERVICE_PORT={OFFCHAIN_SERVICE_PORT}\n")
    dotenv.write(f"NETWORK={NETWORK}\n")
    dotenv.write(f"JSON_RPC_URL={JSON_RPC_URL}\n")
    dotenv.write(f"FAUCET_URL={FAUCET_URL}\n")
    dotenv.write(f"CHAIN_ID={CHAIN_ID}\n")

    init_onchain_account(wallet_custody_private_keys, wallet_account_name, wallet_private_key_hex)

print(f"creating {liquidity_env_file_path}")
# setup liquidity
with open(liquidity_env_file_path, "w") as dotenv:
    lp_account_name = "liquidity"
    private_keys = {f"{lp_account_name}": lp_private_key_hex}
    lp_custody_private_keys = json.dumps(private_keys, separators=(',', ':'))
    dotenv.write(f"LIQUIDITY_CUSTODY_ACCOUNT_NAME=liquidity\n")
    dotenv.write(
        f"CUSTODY_PRIVATE_KEYS={lp_custody_private_keys}\n"
    )

    lp_vasp = init_onchain_account(lp_custody_private_keys, lp_account_name, lp_private_key_hex)

    amount = 999 * 1_000_000
    print('Mint currencies to liquidity account')
    for currency in get_network_supported_currencies():
        print(f'Mint {currency.code}...', end=' ')
        mint_and_wait(lp_vasp.vasp_auth_key, amount, currency.code)
        print(f'mint completed')

    dotenv.write(f"ACCOUNT_WATCHER_AUTH_KEY={lp_vasp.vasp_auth_key}\n")
