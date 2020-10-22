# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from offchainapi.crypto import ComplianceKey

from libra import LocalAccount, utils, testnet

from libra_utils.custody import Custody
from libra_utils.vasp import Vasp
from libra_utils.types.currencies import LibraCurrency

libra_client = testnet.create_client()

wallet_account_name = "wallet"
lp_account_name = "liquidity"


def get_private_key_hex(key: Ed25519PrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()


def init_onchain_account(
    custody_private_keys, account_name, account: LocalAccount, base_url, compliance_key,
):
    account_addr = utils.account_address_hex(account.account_address)
    print(f"Creating and initialize blockchain account {account_name} @ {account_addr}")
    os.environ["CUSTODY_PRIVATE_KEYS"] = custody_private_keys
    Custody.init()
    vasp = Vasp(libra_client, account_name)
    vasp.setup_blockchain(base_url, compliance_key)
    print(f"Account initialization done!")

    return vasp


def mint_all_currencies(account: LocalAccount, amount):
    address_str = utils.account_address_hex(account.account_address)
    faucet = testnet.Faucet(libra_client)

    for currency in libra_client.get_currencies():
        if currency.code == LibraCurrency.Coin1:
            print(f"Minting {amount}{currency.code} for account {address_str}")
            faucet.mint(account.auth_key.hex(), amount, currency.code)


if len(sys.argv) > 2 or len(sys.argv) > 1 and "--help" in sys.argv:
    print(
        """
        
    Setup wallet and liquidity environment including blockchain private keys generation.
    Usage: set_env.py
    Flags: --force      Will regenerate blockchain keys and run current .env configuration.
    """
    )

    exit()

GW_PORT = os.getenv("GW_PORT", 8080)
ENV_FILE_NAME = os.getenv("ENV_FILE_NAME", ".env")
LIQUIDITY_SERVICE_HOST = os.getenv("LIQUIDITY_SERVICE_HOST", "liquidity")
LIQUIDITY_SERVICE_PORT = os.getenv("LIQUIDITY_SERVICE_PORT", 5000)
OFFCHAIN_SERVICE_PORT: int = int(os.getenv("OFFCHAIN_SERVICE_PORT", 8091))
NETWORK = os.getenv("NETWORK", "testnet")
JSON_RPC_URL = os.getenv("JSON_RPC_URL", testnet.JSON_RPC_URL)
FAUCET_URL = os.getenv("FAUCET_URL", testnet.FAUCET_URL)
CHAIN_ID = os.getenv("CHAIN_ID", testnet.CHAIN_ID.value)
VASP_BASE_URL = os.getenv("VASP_BASE_URL", "http://0.0.0.0:8091")
LIQUIDITY_BASE_URL = os.getenv("LIQUIDITY_BASE_URL", "http://0.0.0.0:8092")
VASP_COMPLIANCE_KEY = os.getenv(
    "VASP_COMPLIANCE_KEY", ComplianceKey.generate().export_full()
)
VASP_PUBLIC_KEY_BYTES = (
    ComplianceKey.from_str(VASP_COMPLIANCE_KEY)
        .get_public()
        .public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
)
LIQUIDITY_COMPLIANCE_KEY = os.getenv(
    "LIQUIDITY_COMPLIANCE_KEY", ComplianceKey.generate().export_full()
)
LIQUIDITY_PUBLIC_KEY_BYTES = (
    ComplianceKey.from_str(LIQUIDITY_COMPLIANCE_KEY)
        .get_public()
        .public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
)


if NETWORK == "premainnet":
    vasp = Vasp(libra_client, wallet_account_name)
    vasp_liquidity = Vasp(libra_client, lp_account_name)
    vasp.rotate_dual_attestation_info(VASP_BASE_URL, VASP_PUBLIC_KEY_BYTES)
    vasp_liquidity.rotate_dual_attestation_info(
        LIQUIDITY_BASE_URL, LIQUIDITY_PUBLIC_KEY_BYTES
    )
    exit(0)

wallet_account = LocalAccount.generate()
lp_account = LocalAccount.generate()

execution_dir_path = os.getcwd()
wallet_env_file_path = os.path.join(execution_dir_path, "backend", ENV_FILE_NAME)
liquidity_env_file_path = os.path.join(execution_dir_path, "liquidity", ENV_FILE_NAME)

if os.path.exists(wallet_env_file_path) and os.path.exists(liquidity_env_file_path):
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] != "--force"):
        print(
            f".env variable files are already set.\n run {sys.argv[0]} --force to recreate them"
        )
        exit(0)

print(f"Creating {wallet_env_file_path}")

# setup wallet
with open(wallet_env_file_path, "w") as dotenv:
    private_keys = {
        f"{wallet_account_name}": get_private_key_hex(wallet_account.private_key)
    }
    wallet_custody_private_keys = json.dumps(private_keys, separators=(",", ":"))
    dotenv.write(f"GW_PORT={GW_PORT}\n")
    dotenv.write(f"WALLET_CUSTODY_ACCOUNT_NAME={wallet_account_name}\n")
    dotenv.write(f"CUSTODY_PRIVATE_KEYS={wallet_custody_private_keys}\n")
    dotenv.write(
        f"VASP_ADDR={utils.account_address_hex(wallet_account.account_address)}\n"
    )
    dotenv.write(f"VASP_BASE_URL={VASP_BASE_URL}\n")
    dotenv.write(f"VASP_COMPLIANCE_KEY={VASP_COMPLIANCE_KEY}\n")
    dotenv.write(f"LIQUIDITY_SERVICE_HOST={LIQUIDITY_SERVICE_HOST}\n")
    dotenv.write(f"LIQUIDITY_SERVICE_PORT={LIQUIDITY_SERVICE_PORT}\n")
    dotenv.write(f"OFFCHAIN_SERVICE_PORT={OFFCHAIN_SERVICE_PORT}\n")
    dotenv.write(f"NETWORK={NETWORK}\n")
    dotenv.write(f"JSON_RPC_URL={JSON_RPC_URL}\n")
    dotenv.write(f"FAUCET_URL={FAUCET_URL}\n")
    dotenv.write(f"CHAIN_ID={CHAIN_ID}\n")

    init_onchain_account(
        custody_private_keys=wallet_custody_private_keys,
        account_name=wallet_account_name,
        account=wallet_account,
        base_url=VASP_BASE_URL,
        compliance_key=VASP_PUBLIC_KEY_BYTES,
    )

# setup liquidity
print(f"Creating {liquidity_env_file_path}")
with open(liquidity_env_file_path, "w") as dotenv:
    private_keys = {f"{lp_account_name}": get_private_key_hex(lp_account.private_key)}
    lp_custody_private_keys = json.dumps(private_keys, separators=(",", ":"))
    dotenv.write(f"LIQUIDITY_CUSTODY_ACCOUNT_NAME=liquidity\n")
    dotenv.write(f"CUSTODY_PRIVATE_KEYS={lp_custody_private_keys}\n")
    dotenv.write(
        f"LIQUIDITY_VASP_ADDR={utils.account_address_hex(lp_account.account_address)}\n"
    )
    dotenv.write(f"JSON_RPC_URL={JSON_RPC_URL}\n")
    dotenv.write(f"CHAIN_ID={CHAIN_ID}\n")

    init_onchain_account(
        custody_private_keys=lp_custody_private_keys,
        account_name=lp_account_name,
        account=lp_account,
        base_url=LIQUIDITY_BASE_URL,
        compliance_key=LIQUIDITY_PUBLIC_KEY_BYTES,
    )

    amount = 999 * 1_000_000
    print("Mint currencies to liquidity account")
    mint_all_currencies(lp_account, amount)

    dotenv.write(f"ACCOUNT_WATCHER_AUTH_KEY={lp_account.auth_key.hex()}\n")
