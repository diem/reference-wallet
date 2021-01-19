#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0


from vasp_validator import ValidatorClient
from vasp_validator.models_fppa import FundPullPreApprovalScope
from vasp_validator.vasp_proxy import VaspProxy, TxState


class VaspProxyTestee(VaspProxy):
    """
    This class emulates VASP under test.
    Since, for the testing purposes, both the validator and the testee are
    represented by an instance of the Reference Wallet, this class is just
    a naive wrapper for ValidationClient. We could have used ValidationClient
    directly but then it would have been too confusing.
    """

    def __init__(self, url):
        self.vasp = ValidatorClient.create(url, "pseudo-vasp")

    def get_receiving_address(self) -> str:
        return self.vasp.get_receiving_address()

    def send_transaction(self, address: str, amount: int, currency: str) -> TxState:
        return self.vasp.send_transaction(address, amount, currency)

    def knows_transaction(self, version) -> bool:
        return self.vasp.knows_transaction(version)

    def get_offchain_state(self, reference_id: str):
        return self.vasp.get_offchain_state(reference_id)

    def request_funds_pull_preapproval_from_another(
        self,
        payer_addr_bech32: str,
        scope: FundPullPreApprovalScope,
        description: str = None,
    ) -> str:
        return self.vasp.request_funds_pull_preapproval_from_another(
            payer_addr_bech32, scope, description
        )

    def get_all_funds_pull_preapprovals(self):
        return self.vasp.get_all_funds_pull_preapprovals()
