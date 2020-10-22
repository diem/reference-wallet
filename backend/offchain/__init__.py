# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from offchainapi.core import Vasp
from offchainapi.business import VASPInfo
from offchainapi.libra_address import LibraAddress
from offchainapi.crypto import ComplianceKey
from libra import jsonrpc

from .offchain_business import (
    LRWOffChainBusinessContext,
    VASPInfoNotFoundException,
    BaseURLNotFoundException,
    get_compliance_key_on_chain,
    JSON_RPC_CLIENT,
)

import logging

logger = logging.getLogger(name="offchain.init")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

LRW_VASP_ADDR = LibraAddress.from_hex(os.getenv("VASP_ADDR"))
LRW_VASP_COMPLIANCE_KEY = ComplianceKey.from_str(os.getenv("VASP_COMPLIANCE_KEY"))

print(f"OFFCHAIN SERVICE PORT {os.getenv('OFFCHAIN_SERVICE_PORT')}", flush=True)
OFFCHAIN_SERVICE_PORT: int = int(os.getenv("OFFCHAIN_SERVICE_PORT", 8091))


class LRWSimpleVASPInfo(VASPInfo):
    def __init__(self, my_addr):
        self.my_addr = my_addr

    def get_base_url(self):
        """ Get the base URL that manages off-chain communications.
            Returns:
                str: The base url of the VASP.
        """
        return os.getenv("VASP_BASE_URL")

    def get_peer_base_url(self, other_addr):
        """ Get the base URL that manages off-chain communications of the other
            VASP.
            Args:
                other_addr (LibraAddress): The Libra Blockchain address of the other VASP.
            Returns:
                str: The base url of the other VASP.
        """
        other_vasp_addr = other_addr.get_onchain_address_hex()
        account = JSON_RPC_CLIENT.get_account(other_vasp_addr)
        if account is None:
            raise VASPInfoNotFoundException(
                f"VASP account {other_vasp_addr} was not found onchain"
            )

        if account.role.type == jsonrpc.ACCOUNT_ROLE_CHILD_VASP:
            parent_vasp_addr = account.role.parent_vasp_address
            account = JSON_RPC_CLIENT.get_account(parent_vasp_addr)
            if account is None:
                raise VASPInfoNotFoundException(
                    f"VASP account {parent_vasp_addr} was not found onchain"
                )

        base_url: str = account.role.base_url
        logger.debug(f"got base_url {base_url}")

        if not base_url:
            raise BaseURLNotFoundException(
                f"Base URL is empty for peer vasp {account.address}"
            )
        return base_url

    def get_libra_address(self):
        """ The settlement Libra Blockchain address for this channel.
            Returns:
                LibraAddress: The Libra Blockchain address.
        """
        raise NotImplementedError()  # pragma: no cover

    def get_parent_address(self):
        """ The VASP Parent address for this channel. High level logic is common
        to all Libra Blockchain addresses under a parent to ensure consistency and
        compliance.
        Returns:
            LibraAddress: The Libra Blockchain address of the parent VASP.
        """
        raise NotImplementedError()  # pragma: no coverv

    def is_unhosted(self, other_addr):
        """ Returns True if the other party is an unhosted wallet.
            Args:
                other_addr (LibraAddress): The Libra Blockchain address of the other VASP.
            Returns:
                bool: Whether the other VASP is an unhosted wallet.
        """
        return False

    def get_peer_compliance_verification_key(self, other_addr):
        """ Returns the compliance verfication key of the other VASP.
        Args:
            other_addr (LibraAddress): The Libra Blockchain address of the other VASP.
        Returns:
            ComplianceKey: The compliance verification key of the other VASP.
        """
        logger.debug(f"get_peer_compliance_verification_key {other_addr}")
        libra_address = LibraAddress.from_encoded_str(
            other_addr
        ).get_onchain_address_hex()
        logger.debug(f"get_peer_compliance_verification_key libra addr {libra_address}")
        return get_compliance_key_on_chain(libra_address)

    def get_my_compliance_signature_key(self, my_addr):
        """ Returns the compliance signature (secret) key of the VASP.
        Args:
            my_addr (LibraAddress): The Libra Blockchain address of the VASP.
        Returns:
            ComplianceKey: The compliance key of the VASP.
        """
        return LRW_VASP_COMPLIANCE_KEY


def make_new_VASP(Peer_addr, reliable=True):
    return Vasp(
        Peer_addr,
        host="0.0.0.0",
        port=OFFCHAIN_SERVICE_PORT,
        business_context=LRWOffChainBusinessContext(Peer_addr, reliable=reliable),
        info_context=LRWSimpleVASPInfo(Peer_addr),
        database={},
    )
