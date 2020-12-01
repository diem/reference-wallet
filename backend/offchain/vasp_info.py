# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from context import Context
from dataclasses import dataclass

from offchainapi.business import VASPInfo
from offchainapi.crypto import ComplianceKey
from offchainapi.libra_address import LibraAddress


@dataclass
class LRW(VASPInfo):
    context: Context

    def get_peer_base_url(self, other_addr: LibraAddress) -> str:
        """ Get the base URL that manages off-chain communications of the other
            VASP.
            Returns:
                str: The base url of the other VASP.
        """

        return self.context.get_vasp_base_url(other_addr.get_onchain_address_hex())

    def get_peer_compliance_verification_key(self, other_addr: str) -> ComplianceKey:
        address = LibraAddress.from_encoded_str(other_addr).get_onchain_address_hex()
        return self.context.get_vasp_public_compliance_key(address)

    def get_my_compliance_signature_key(self, my_addr) -> ComplianceKey:
        return self.context.config.offchain_compliance_key()
