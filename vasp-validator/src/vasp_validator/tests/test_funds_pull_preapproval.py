#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import os
import time

from ..vasp_proxy import VaspProxy
from ..models_fppa import (
    FundsPullPreApproval,
    FundPullPreApprovalScope,
    FundPullPreApprovalType,
    FundPullPreApprovalStatus,
)

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60

RETRIES_COUNT = os.getenv("RETRIES_COUNT", 10)
SECONDS_BETWEEN_RETRIES = os.getenv("SECONDS_BETWEEN_RETRIES", 1)


def create_preapproval_validator(vasp: VaspProxy, fppa_id: str):
    def get_and_assert_one_preapproval(
        status: FundPullPreApprovalStatus,
    ) -> FundsPullPreApproval:
        preapproval = None

        for i in range(RETRIES_COUNT):
            preapprovals = vasp.get_all_funds_pull_preapprovals()

            assert len(preapprovals) == 1

            preapproval = preapprovals[0]
            assert preapproval.funds_pull_pre_approval_id == fppa_id

            if preapproval.status == status:
                return preapproval

            time.sleep(SECONDS_BETWEEN_RETRIES)

        assert preapproval.status == status

    return get_and_assert_one_preapproval


def test_request_approve_close(validator, vasp_proxy: VaspProxy):
    """
    The VASP receives a funds pull pre-approval request, approves and then closes it.
    """

    # Step 1: Create the request and validate it's "pending" on both sides
    actual_id = validator.request_funds_pull_preapproval_from_another(
        payer_addr_bech32=vasp_proxy.get_receiving_address(),
        description="test_request_approve_cancel",
        scope=FundPullPreApprovalScope(
            type=FundPullPreApprovalType.consent,
            expiration_timestamp=int(time.time()) + ONE_YEAR_SECONDS,
        ),
    )

    assert_validator_preapproval = create_preapproval_validator(validator, actual_id)
    assert_vasp_preapproval = create_preapproval_validator(vasp_proxy, actual_id)

    validator_fppa = assert_validator_preapproval(FundPullPreApprovalStatus.pending)
    vasp_fppa = assert_vasp_preapproval(FundPullPreApprovalStatus.pending)
    assert vasp_fppa == validator_fppa

    # Step 2: Approve the request and validate it is "valid" on both sides
    vasp_proxy.approve_funds_pull_request(actual_id)
    assert_validator_preapproval(FundPullPreApprovalStatus.valid)
    assert_vasp_preapproval(FundPullPreApprovalStatus.valid)

    # Step 3: Close the approved request and validate it is "closed" on both sides
    vasp_proxy.close_funds_pull_preapproval(actual_id)
    assert_validator_preapproval(FundPullPreApprovalStatus.closed)
    assert_vasp_preapproval(FundPullPreApprovalStatus.closed)


def test_request_and_reject(validator, vasp_proxy: VaspProxy):
    """
    The VASP receives a funds pull pre-approval request and rejects it.
    """

    # Step 1: Create the request and validate it's "pending" on both sides
    actual_id = validator.request_funds_pull_preapproval_from_another(
        payer_addr_bech32=vasp_proxy.get_receiving_address(),
        description="test_request_and_reject",
        scope=FundPullPreApprovalScope(
            type=FundPullPreApprovalType.consent,
            expiration_timestamp=int(time.time()) + ONE_YEAR_SECONDS,
        ),
    )

    assert_validator_preapproval = create_preapproval_validator(validator, actual_id)
    assert_vasp_preapproval = create_preapproval_validator(vasp_proxy, actual_id)

    validator_fppa = assert_validator_preapproval(FundPullPreApprovalStatus.pending)
    vasp_fppa = assert_vasp_preapproval(FundPullPreApprovalStatus.pending)
    assert vasp_fppa == validator_fppa

    # Step 2: reject the request and validate it is "valid" on both sides
    vasp_proxy.reject_funds_pull_request(actual_id)
    assert_validator_preapproval(FundPullPreApprovalStatus.rejected)
    assert_vasp_preapproval(FundPullPreApprovalStatus.rejected)


def test_approve_request_by_payer(validator, vasp_proxy: VaspProxy):
    """
    The VASP receives a funds pull pre-approval request details and approve it
    """
    # Step 1: Trigger the request creation in the validator
    # and validate it's been created with "pending" status
    # and validate that no request was created in vasp_proxy
    scope = FundPullPreApprovalScope(
        type=FundPullPreApprovalType.consent,
        expiration_timestamp=int(time.time()) + ONE_YEAR_SECONDS,
    )
    description = "test_approve_request_by_payer"
    (actual_id, validator_address,) = validator.create_fppa_request_for_unknown_payer(
        description=description,
        scope=scope,
    )

    assert len(vasp_proxy.get_all_funds_pull_preapprovals()) == 0

    assert_validator_preapproval = create_preapproval_validator(validator, actual_id)

    assert_validator_preapproval(FundPullPreApprovalStatus.pending)

    # Step 2: Create and approve the request in vasp_proxy
    # and validate it is "valid" on both sides
    vasp_proxy.create_and_approve_funds_pull_request(
        biller_address=validator_address,
        funds_pull_pre_approval_id=actual_id,
        scope=scope,
        description=description,
    )
    assert_vasp_preapproval = create_preapproval_validator(vasp_proxy, actual_id)
    assert_vasp_preapproval(FundPullPreApprovalStatus.valid)
    assert_validator_preapproval(FundPullPreApprovalStatus.valid)
