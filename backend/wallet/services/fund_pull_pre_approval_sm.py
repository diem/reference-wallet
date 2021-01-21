#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from diem.offchain import FundPullPreApprovalStatus

from wallet.storage.funds_pull_pre_approval_command import (
    commit_command,
    update_command,
)


class FundsPullPreApprovalError(Exception):
    ...


class Role(str, Enum):
    PAYEE = "payee"
    PAYER = "payer"


def get_role(
    incoming_status: str,
    is_payee_address_mine: bool,
    is_payer_address_mine: bool,
    existing_status_as_payee: Optional[str],
    existing_status_as_payer: Optional[str],
) -> Role:
    combination = Combination(
        incoming_status=incoming_status,
        is_payee_address_mine=is_payee_address_mine,
        is_payer_address_mine=is_payer_address_mine,
        existing_status_as_payee=existing_status_as_payee,
        existing_status_as_payer=existing_status_as_payer,
    )

    combinations = get_combinations()

    role = combinations.get(combination)

    if role is None:
        raise FundsPullPreApprovalError()

    return role


@dataclass(frozen=True)
class Combination:
    incoming_status: str
    is_payee_address_mine: bool
    is_payer_address_mine: bool
    existing_status_as_payee: Optional[str]
    existing_status_as_payer: Optional[str]

    @property
    def is_incoming_valid_or_rejected(self) -> bool:
        return self.incoming_status in [
            FundPullPreApprovalStatus.valid,
            FundPullPreApprovalStatus.rejected,
        ]

    @property
    def is_incoming_pending(self) -> bool:
        return self.incoming_status is FundPullPreApprovalStatus.pending

    @property
    def is_incoming_closed(self) -> bool:
        return self.incoming_status is FundPullPreApprovalStatus.closed

    @property
    def both_mine(self):
        return self.is_payer_address_mine and self.is_payee_address_mine

    @property
    def preapproval_exists(self):
        return (
            self.existing_status_as_payer is not None
            or self.existing_status_as_payee is not None
        )

    @property
    def payer_preapproval_exists(self):
        return self.existing_status_as_payee is not None

    @property
    def is_payee_pending(self):
        return self.existing_status_as_payee is FundPullPreApprovalStatus.pending

    @property
    def is_payee_closed(self):
        return self.existing_status_as_payee is FundPullPreApprovalStatus.closed

    @property
    def is_payee_valid(self):
        return self.existing_status_as_payee is FundPullPreApprovalStatus.valid

    @property
    def is_payer_pending(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.pending

    @property
    def is_payer_closed(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.closed

    @property
    def is_payer_valid(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.valid


def get_combinations():
    Incoming = FundPullPreApprovalStatus
    Existing = FundPullPreApprovalStatus

    # fmt: off
    explicit_combinations = {
        # only payer can receive 'pending'
        Combination(Incoming.pending, True, True, Existing.pending, None): Role.PAYER,  # new request from known payee
        Combination(Incoming.pending, True, True, Existing.pending, Existing.pending): Role.PAYER,  # update request from known payee
        Combination(Incoming.pending, False, True, None, None): Role.PAYER,  # new request from unknown payee
        Combination(Incoming.pending, False, True, None, Existing.pending): Role.PAYER,  # update request from unknown payee
        # only payee can receive 'valid'
        Combination(Incoming.valid, True, False, Existing.pending, None): Role.PAYEE,  # approve request by unknown payer
        Combination(Incoming.valid, True, True, Existing.pending, Existing.valid): Role.PAYEE, # get approve from known payer
        # only payee can receive 'rejected'
        Combination(Incoming.rejected, True, False, Existing.pending, None): Role.PAYEE,  # reject request by unknown payer
        Combination(Incoming.rejected, True, True, Existing.pending, Existing.rejected): Role.PAYEE,  # reject request by known payer
        #
        Combination(Incoming.closed, False, True, None, Existing.pending): Role.PAYER,  # close 'pending' request by unknown payee
        Combination(Incoming.closed, False, True, None, Existing.valid): Role.PAYER,  # close 'valid' request by unknown payee
        #
        Combination(Incoming.closed, True, True, Existing.closed, Existing.pending): Role.PAYER,  # close request by known payee
        Combination(Incoming.closed, True, True, Existing.closed, Existing.valid): Role.PAYER,  # close request by known payee
        #
        Combination(Incoming.closed, True, False, Existing.pending, None): Role.PAYEE,  # close 'pending' request by unknown payer
        Combination(Incoming.closed, True, False, Existing.valid, None): Role.PAYEE,  # close 'valid' request by unknown payer
        #
        Combination(Incoming.closed, True, True, Existing.pending, Existing.closed): Role.PAYEE,  # close request by known payer
        Combination(Incoming.closed, True, True, Existing.valid, Existing.closed): Role.PAYEE,  # close request by known payer
        #
        Combination(Incoming.pending, False, True, None, Existing.valid): None,
        Combination(Incoming.pending, False, True, None, Existing.closed): None,
        Combination(Incoming.pending, False, True, None, Existing.rejected): None,
        Combination(Incoming.closed, False, True, None, Existing.rejected): None,
        Combination(Incoming.closed, False, True, None, Existing.closed): None,
        Combination(Incoming.closed, True, False, Existing.closed, None): None,
        Combination(Incoming.closed, True, False, Existing.rejected, None): None,
    }

    all_combinations_ = {}

    all_combinations_.update(make_error_combinations(payee_and_payer_not_mine()))
    all_combinations_.update(make_error_combinations(basic_invalid_states()))
    all_combinations_.update(
        make_error_combinations(incoming_status_not_pending_and_no_records())
    )
    all_combinations_.update(make_error_combinations(incoming_pending_for_payee()))
    all_combinations_.update(
        make_error_combinations(incoming_valid_or_rejected_but_payee_not_pending())
    )
    all_combinations_.update(
        make_error_combinations(
            incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming()
        )
    )
    all_combinations_.update(
        make_error_combinations(
            incoming_pending_my_payee_not_pending_my_payer_pending_or_none()
        )
    )
    all_combinations_.update(
        make_error_combinations(invalid_states_for_incoming_closed())
    )

    all_combinations_.update(explicit_combinations)
    # fmt: on

    return all_combinations_


def all_combinations():
    statuses = [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ]

    for incoming_status in statuses:
        for is_payee_address_mine in [True, False]:
            for is_payer_address_mine in [True, False]:
                for existing_status_as_payee in statuses + [None]:
                    for existing_status_as_payer in statuses + [None]:
                        yield Combination(
                            incoming_status,
                            is_payee_address_mine,
                            is_payer_address_mine,
                            existing_status_as_payee,
                            existing_status_as_payer,
                        )


def payee_and_payer_not_mine():
    return [
        combination for combination in all_combinations() if not combination.both_mine
    ]


def basic_invalid_states():
    """
    basic states that are not valid:
    1. payee is not mine but record exist
    (OR)
    2. payer is not mine but record exist
    """
    return [
        combination
        for combination in all_combinations()
        if (
            not combination.is_payee_address_mine
            and combination.existing_status_as_payee is not None
        )
        or (
            not combination.is_payer_address_mine
            and combination.existing_status_as_payer is not None
        )
    ]


def incoming_status_not_pending_and_no_records():
    return [
        combination
        for combination in all_combinations()
        if not combination.is_incoming_pending and not combination.preapproval_exists
    ]


def incoming_pending_for_payee():
    # if incoming status is 'pending', the payer address is not mine
    # and the payee address is mine all combinations are invalid
    return [
        combination
        for combination in all_combinations()
        if not combination.is_payer_address_mine
        and combination.is_payee_address_mine
        and combination.is_incoming_pending
    ]


def incoming_valid_or_rejected_but_payee_not_pending():
    return [
        combination
        for combination in all_combinations()
        if combination.is_incoming_valid_or_rejected
        and not combination.is_payee_pending
    ]


# both role are mine, incoming status is 'valid' or 'rejected',
# payee must be 'pending' and payer must be equals to incoming status
def incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming():
    return [
        combination
        for combination in all_combinations()
        if combination.both_mine
        and combination.is_incoming_valid_or_rejected
        and combination.is_payee_pending
        and combination.existing_status_as_payer != combination.incoming_status
    ]


# if payer none or pending --> payee must be pending
# if payee pending --> payer must be none or pending
def incoming_pending_my_payee_not_pending_my_payer_pending_or_none():
    """
    'pending' commands only payee can send, therefore when both 'mine' and incoming status is 'pending' the payee
    must had been save his command in the DB before sending. only 2 scenarios are valid in the payer side:
    1. receiving completely new command and therefore no record in DB.
    2. receiving update to existing command and therefore record with status 'pending' exist in DB
    following this a number of states are define as invalid for incoming 'pending' status:
    1. payee don't have record or record exist with status not 'pending'
    2. payer have record with status not 'pending'
    """
    return [
        combination
        for combination in all_combinations()
        if combination.both_mine
        and (
            not combination.is_payee_pending
            or (
                combination.is_payee_pending
                and not combination.is_payer_pending
                and combination.payer_preapproval_exists
            )
        )
    ]


def invalid_states_for_incoming_closed():
    """
    when both 'mine' and incoming status is 'closed' the side who sent the command must had been save his update in
    the DB before sending, following this a number of states are define as invalid for incoming closed status:
    1. both not 'closed' in DB
    2. payee 'closed' but payer not 'pending' or 'valid'
    3. payer 'closed' but payee not 'pending' or 'valid'
    """
    return [
        combination
        for combination in all_combinations()
        if combination.both_mine
        and combination.is_incoming_closed
        and (
            (not combination.is_payee_closed and not combination.is_payee_closed)
            or (
                (
                    combination.is_payee_closed
                    and not combination.is_payee_pending
                    and not combination.is_payee_valid
                )
                or (
                    combination.is_payee_closed
                    and not combination.is_payer_pending
                    and not combination.is_payer_valid
                )
            )
        )
    ]


def make_error_combinations(combinations) -> dict:
    return {combination: None for combination in combinations}


@dataclass(frozen=True)
class Option:
    role: str
    incoming_status: str
    status_in_db: Optional[str]


def get_next_action(
    role: str,
    incoming_status: str,
    status_in_db: Optional[str],
):
    # fmt: off
    options = {
        Option(Role.PAYER, FundPullPreApprovalStatus.pending, None): commit_command,
        Option(Role.PAYER, FundPullPreApprovalStatus.pending, FundPullPreApprovalStatus.pending): update_command,
        Option(Role.PAYER, FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.pending): update_command,
        Option(Role.PAYER, FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.valid): update_command,
        Option(Role.PAYEE, FundPullPreApprovalStatus.valid, FundPullPreApprovalStatus.pending): update_command,
        Option(Role.PAYEE, FundPullPreApprovalStatus.rejected, FundPullPreApprovalStatus.pending): update_command,
        Option(Role.PAYEE, FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.pending): update_command,
        Option(Role.PAYEE, FundPullPreApprovalStatus.closed, FundPullPreApprovalStatus.valid): update_command,
    }
    # fmt: on

    option = Option(role, incoming_status, status_in_db)

    if option in options:
        return options.get(option)
    else:
        raise FundsPullPreApprovalError(f"Failed to find action for option {option}")
