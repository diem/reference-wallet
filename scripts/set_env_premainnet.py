#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

import json
import os

from diem.utils import public_key_bytes

import context

ENV_FILE_NAME = os.getenv("ENV_FILE_NAME", ".env")

GW_PORT = int(os.getenv("GW_PORT", 8080))
VASP_BASE_URL = os.getenv("VASP_BASE_URL", "http://localhost:5000/offchain")
LIQUIDITY_SERVICE_HOST = os.getenv("LIQUIDITY_SERVICE_HOST", "liquidity")
LIQUIDITY_SERVICE_PORT = int(os.getenv("LIQUIDITY_SERVICE_PORT", 5000))
ACCOUNT_PRIVATE_KEY = os.environ["WALLET_ACCOUNT_PRIVATE_KEY"]

PREMAINNET_JSON_RPC_URL = "https://premainnet.diem.com/v1"
PREMAINNET_CHAIN_ID = 21


def validate_vasp_account_existence(ctx: context.Context):
    ctx.jsonrpc_client.must_get_account(ctx.config.vasp_account_address())


def validate_vasp_attestation_info(ctx: context.Context):
    actual_url, actual_compliance_key = ctx.jsonrpc_client.get_base_url_and_compliance_key(
        ctx.config.vasp_account_address()
    )

    if actual_url != ctx.config.base_url:
        raise Exception(
            f"Inconsistent attestation info. "
            f"Expected {ctx.config.base_url} but found on chain {actual_url}"
        )

    actual_compliance_key = public_key_bytes(actual_compliance_key).hex()
    expected_key = ctx.config.compliance_public_key_bytes().hex()
    if actual_compliance_key != expected_key:
        raise Exception(
            f"Inconsistent attestation info. "
            f"Expected {expected_key} but found on chain {actual_compliance_key}"
        )


def to_compact_json(d: dict) -> str:
    return json.dumps(d, separators=(",", ":"))


def write_dotenv(ctx: context.Context):
    wallet_env_file_path = os.path.join(os.getcwd(), "backend", ENV_FILE_NAME)
    print(f"Creating {wallet_env_file_path}")

    wallet_account_name = ctx.config.wallet_custody_account_name
    wallet_custody_private_keys = to_compact_json({
        wallet_account_name: ACCOUNT_PRIVATE_KEY
    })

    with open(wallet_env_file_path, "w") as dotenv:
        dotenv.write(f"GW_PORT={GW_PORT}\n")
        dotenv.write(f"WALLET_CUSTODY_ACCOUNT_NAME={wallet_account_name}\n")
        dotenv.write(f"CUSTODY_PRIVATE_KEYS={wallet_custody_private_keys}\n")
        dotenv.write(
            f"VASP_ADDR={ctx.config.vasp_address}\n"
        )
        dotenv.write(f"VASP_BASE_URL={ctx.config.base_url}\n")
        dotenv.write(f"VASP_COMPLIANCE_KEY={ctx.config.vasp_compliance_key}\n")
        dotenv.write(f"JSON_RPC_URL={ctx.config.json_rpc_url}\n")
        dotenv.write(f"CHAIN_ID={ctx.config.chain_id}\n")
        dotenv.write(f"GAS_CURRENCY_CODE={ctx.config.gas_currency_code}\n")

        dotenv.write(f"LIQUIDITY_SERVICE_HOST={LIQUIDITY_SERVICE_HOST}\n")
        dotenv.write(f"LIQUIDITY_SERVICE_PORT={LIQUIDITY_SERVICE_PORT}\n")


def main():
    ctx = context.generate(
        index=1,
        vasp_private_key=ACCOUNT_PRIVATE_KEY,
        json_rpc_url=PREMAINNET_JSON_RPC_URL,
        chain_id=PREMAINNET_CHAIN_ID,
    )
    validate_vasp_account_existence(ctx)
    print("Premainnet account is valid")

    ctx.reset_dual_attestation_info()
    validate_vasp_attestation_info(ctx)
    print("Attestation info is correct")

    print("Saving configuration")
    write_dotenv(ctx)


if __name__ == "__main__":
    main()
