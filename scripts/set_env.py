# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import sys
import os
import subprocess
import re
import json
from secrets import token_bytes
from pylibra import AccountKeyUtils


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
NETWORK = os.getenv("NETWORK", "testnet")
JSON_RPC_URL = os.getenv("JSON_RPC_URL", "https://testnet.libra.org/v1")
FAUCET_URL = os.getenv("FAUCET_URL", "http://testnet.libra.org/mint")
CHAIN_ID = os.getenv("CHAIN_ID", 2)

wallet_private_key_hex: str = token_bytes(32).hex()
liquidity_private_key_hex: str = token_bytes(32).hex()

execution_dir_path = os.getcwd()


def public_libra_address_from_key_hex(private_key_hex):
    private_key_bytes: bytes = bytes.fromhex(private_key_hex)
    return AccountKeyUtils.from_private_key(private_key_bytes).address.hex()

result = subprocess.run(["docker-compose", "--version"], capture_output=True)
matching_version = re.match(r"docker-compose version (\d\.\d+).*", result.stdout.decode())
docker_compose_version = float(matching_version.groups()[0])
use_direct_names = False
if docker_compose_version < 1.26:
    print(f"docker-compose version is under 1.26 [{docker_compose_version}]. upgrade is recommended. falling back to 1.25 syntax...")
    use_direct_names = True

wallet_env_file_path = os.path.join(execution_dir_path, "backend", ENV_FILE_NAME)
liquidity_env_file_path = os.path.join(execution_dir_path, "liquidity", ENV_FILE_NAME)

if os.path.exists(wallet_env_file_path) and os.path.exists(liquidity_env_file_path):
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] != '--force'):
        print(f".env variable files are already set.\n run {sys.argv[0]} --force to recreate them")
        exit(0)

print(f"creating {wallet_env_file_path}")

# setup wallet
with open(wallet_env_file_path, "w") as dotenv:
    account_name = "wallet"
    private_keys = {"${WALLET_CUSTODY_ACCOUNT_NAME}": wallet_private_key_hex}
    if use_direct_names:
        private_keys = {f"{account_name}": wallet_private_key_hex}
    dotenv.write(f"GW_PORT={GW_PORT}\n")
    dotenv.write(f"WALLET_CUSTODY_ACCOUNT_NAME={account_name}\n")
    dotenv.write(
        f"CUSTODY_PRIVATE_KEYS={json.dumps(private_keys, separators=(',', ':'))}\n"
    )
    dotenv.write(
        f"VASP_ADDR={public_libra_address_from_key_hex(wallet_private_key_hex)}\n"
    )
    dotenv.write(f"NETWORK={NETWORK}\n")
    dotenv.write(f"LIQUIDITY_SERVICE_HOST={LIQUIDITY_SERVICE_HOST}\n")
    dotenv.write(f"LIQUIDITY_SERVICE_PORT={LIQUIDITY_SERVICE_PORT}\n")
    dotenv.write(f"JSON_RPC_URL={JSON_RPC_URL}\n")
    dotenv.write(f"FAUCET_URL={FAUCET_URL}\n")
    dotenv.write(f"CHAIN_ID={CHAIN_ID}\n")

print(f"creating {liquidity_env_file_path}")

# setup wallet
with open(liquidity_env_file_path, "w") as dotenv:
    account_name = "liquidity"
    private_keys = {"${LIQUIDITY_CUSTODY_ACCOUNT_NAME}": liquidity_private_key_hex}
    if use_direct_names:
        private_keys = {f"{account_name}": liquidity_private_key_hex}
    dotenv.write(f"LIQUIDITY_CUSTODY_ACCOUNT_NAME=liquidity\n")
    dotenv.write(
        f"CUSTODY_PRIVATE_KEYS={json.dumps(private_keys, separators=(',', ':'))}\n"
    )
