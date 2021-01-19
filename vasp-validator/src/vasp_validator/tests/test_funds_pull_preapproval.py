#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import time

from ..vasp_proxy import VaspProxy
from ..models_fppa import (
    FundsPullPreApproval,
    FundPullPreApprovalScope,
    FundPullPreApprovalType,
    FundPullPreApprovalStatus,
)

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def get_and_assert_one_preapproval(
    vasp: VaspProxy, fppa_id: str, status: FundPullPreApprovalStatus
) -> FundsPullPreApproval:
    preapprovals = vasp.get_all_funds_pull_preapprovals()
    assert len(preapprovals) == 1

    preapproval = preapprovals[0]
    assert preapproval.funds_pull_pre_approval_id == fppa_id
    assert preapproval.status == status

    return preapproval


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

    validator_preapproval = get_and_assert_one_preapproval(
        validator, actual_preapproval_id, FundPullPreApprovalStatus.pending
    )
    vasp_preapproval = get_and_assert_one_preapproval(
        vasp_proxy, actual_preapproval_id, FundPullPreApprovalStatus.pending
    )
    assert vasp_preapproval == validator_preapproval
