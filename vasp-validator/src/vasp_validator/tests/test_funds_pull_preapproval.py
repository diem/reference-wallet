#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import time

from ..vasp_proxy import VaspProxy
from ..models_fppa import FundPullPreApprovalScope, FundPullPreApprovalType, FundPullPreApprovalStatus

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def test_receive_request_and_approve(validator, vasp_proxy: VaspProxy):
    """
    The VASP receives a funds pull pre-approval request and approves it.
    """
    actual_preapproval_id = validator.request_funds_pull_preapproval_from_another(
        payer_addr_bech32=vasp_proxy.get_receiving_address(),
        description="test_receive_request_and_approve",
        scope=FundPullPreApprovalScope(
            type=FundPullPreApprovalType.consent,
            expiration_timestamp=int(time.time()) + ONE_YEAR_SECONDS,
        ),
    )

    validator_preapprovals = validator.get_all_funds_pull_preapprovals()
    assert len(validator_preapprovals) == 1
    assert validator_preapprovals[0].funds_pull_pre_approval_id == actual_preapproval_id
    assert validator_preapprovals[0].status == FundPullPreApprovalStatus.pending

    time.sleep(2)

    vasp_preapprovals = vasp_proxy.get_all_funds_pull_preapprovals()
    assert len(vasp_preapprovals) == 1
    assert vasp_preapprovals[0] == validator_preapprovals[0]

