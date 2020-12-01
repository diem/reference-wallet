# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import typing

from os import getenv, environ
from dataclasses import dataclass
from diem import diem_types, testnet, utils, LocalAccount, identifier
from offchainapi.libra_address import LibraAddress
from offchainapi.crypto import ComplianceKey


@dataclass
class Config:
    # vasp_address should be address for a ParentVASP account
    vasp_address: str
    wallet_custody_account_name: str
    vasp_compliance_key: str
    json_rpc_url: str
    offchain_service_port: int
    base_url: str
    chain_id: int
    gas_currency_code: str

    def vasp_account_address(self) -> diem_types.AccountAddress:
        return utils.account_address(self.vasp_address)

    def vasp_diem_address(self) -> LibraAddress:
        return LibraAddress.from_hex(self.diem_address_hrp(), self.vasp_address, None)

    def diem_address_hrp(self) -> str:
        return identifier.HRPS[self.chain_id]

    def offchain_compliance_key(self) -> ComplianceKey:
        return ComplianceKey.from_str(self.vasp_compliance_key)

    def compliance_public_key_bytes(self) -> bytes:
        pub = self.offchain_compliance_key().get_public()
        return utils.public_key_bytes(pub)


def from_env() -> Config:
    return Config(
        vasp_address=environ["VASP_ADDR"],
        wallet_custody_account_name=environ["WALLET_CUSTODY_ACCOUNT_NAME"],
        vasp_compliance_key=environ["VASP_COMPLIANCE_KEY"],
        json_rpc_url=environ["JSON_RPC_URL"],
        offchain_service_port=int(environ["OFFCHAIN_SERVICE_PORT"]),
        base_url=environ["VASP_BASE_URL"],
        chain_id=int(environ["CHAIN_ID"]),
        gas_currency_code=environ["GAS_CURRENCY_CODE"],
    )


def generate(index: int) -> typing.Tuple[LocalAccount, Config]:
    port = 5090 + index
    base_url = f"http://localhost:{port}"
    account = LocalAccount.generate()
    conf = Config(
        wallet_custody_account_name=f"wallet{index}",
        vasp_compliance_key=ComplianceKey.generate().export_full(),
        vasp_address=account.account_address.to_hex(),
        offchain_service_port=port,
        base_url=base_url,
        json_rpc_url=testnet.JSON_RPC_URL,
        chain_id=testnet.CHAIN_ID.to_int(),
        gas_currency_code=testnet.TEST_CURRENCY_CODE,
    )
    return (account, conf)
