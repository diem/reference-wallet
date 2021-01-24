#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from diem.offchain import FundPullPreApprovalStatus


class FundsPullPreApprovalError(Exception):
    ...


class Role(str, Enum):
    PAYEE = "payee"
    PAYER = "payer"


def reduce_role(
    incoming_status: str,
    is_payee_address_mine: bool,
    is_payer_address_mine: bool,
    existing_status_as_payee: Optional[str],
    existing_status_as_payer: Optional[str],
) -> Role:
    state = FppaState(
        incoming_status=incoming_status,
        is_payee_address_mine=is_payee_address_mine,
        is_payer_address_mine=is_payer_address_mine,
        existing_status_as_payee=existing_status_as_payee,
        existing_status_as_payer=existing_status_as_payer,
    )
    return _reduce_role(state)


@dataclass(frozen=True)
class FppaState:
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


def build_role_reducer():
    Incoming = FundPullPreApprovalStatus
    Existing = FundPullPreApprovalStatus

    # fmt: off
    explicit_states = {
        # only payer can receive 'pending'
        FppaState(Incoming.pending, True, True, Existing.pending, None): Role.PAYER,  # new request from known payee
        FppaState(Incoming.pending, True, True, Existing.pending, Existing.pending): Role.PAYER,  # update request from known payee
        FppaState(Incoming.pending, False, True, None, None): Role.PAYER,  # new request from unknown payee
        FppaState(Incoming.pending, False, True, None, Existing.pending): Role.PAYER,  # update request from unknown payee
        # only payee can receive 'valid'
        FppaState(Incoming.valid, True, False, Existing.pending, None): Role.PAYEE,  # approve request by unknown payer
        FppaState(Incoming.valid, True, True, Existing.pending, Existing.valid): Role.PAYEE, # get approve from known payer
        # only payee can receive 'rejected'
        FppaState(Incoming.rejected, True, False, Existing.pending, None): Role.PAYEE,  # reject request by unknown payer
        FppaState(Incoming.rejected, True, True, Existing.pending, Existing.rejected): Role.PAYEE,  # reject request by known payer
        #
        FppaState(Incoming.closed, False, True, None, Existing.pending): Role.PAYER,  # close 'pending' request by unknown payee
        FppaState(Incoming.closed, False, True, None, Existing.valid): Role.PAYER,  # close 'valid' request by unknown payee
        #
        FppaState(Incoming.closed, True, True, Existing.closed, Existing.pending): Role.PAYER,  # close request by known payee
        FppaState(Incoming.closed, True, True, Existing.closed, Existing.valid): Role.PAYER,  # close request by known payee
        #
        FppaState(Incoming.closed, True, False, Existing.pending, None): Role.PAYEE,  # close 'pending' request by unknown payer
        FppaState(Incoming.closed, True, False, Existing.valid, None): Role.PAYEE,  # close 'valid' request by unknown payer
        #
        FppaState(Incoming.closed, True, True, Existing.pending, Existing.closed): Role.PAYEE,  # close request by known payer
        FppaState(Incoming.closed, True, True, Existing.valid, Existing.closed): Role.PAYEE,  # close request by known payer
        #
        FppaState(Incoming.closed, False, True, None, Existing.rejected): None,
        FppaState(Incoming.closed, False, True, None, Existing.closed): None,
        FppaState(Incoming.closed, True, False, Existing.closed, None): None,
        FppaState(Incoming.closed, True, False, Existing.rejected, None): None,
    }

    all_states = {}

    all_states.update(make_error_combinations(payee_and_payer_not_mine()))
    all_states.update(make_error_combinations(payee_not_mine_but_has_record()))
    all_states.update(make_error_combinations(payer_not_mine_but_has_record()))
    all_states.update(make_error_combinations(incoming_status_not_pending_and_no_records()))
    all_states.update(make_error_combinations(incoming_pending_for_payee_payer_not_mine()))
    all_states.update(make_error_combinations(incoming_pending_for_non_pending_payer()))
    all_states.update(make_error_combinations(incoming_pending_non_pending_payee_payer_mine()))
    all_states.update(make_error_combinations(incoming_valid_or_rejected_but_payee_not_pending()))
    all_states.update(make_error_combinations(incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming()))
    all_states.update(make_error_combinations(invalid_states_for_incoming_closed()))

    all_states.update(explicit_states)
    # fmt: on

    def reducer(state: FppaState) -> Role:
        role = all_states[state]

        if role is None:
            raise FundsPullPreApprovalError()

        return role

    return reducer


def make_error_combinations(states) -> dict:
    return {state: None for state in states}


def all_possible_states():
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
                        yield FppaState(
                            incoming_status,
                            is_payee_address_mine,
                            is_payer_address_mine,
                            existing_status_as_payee,
                            existing_status_as_payer,
                        )


_all_possible_states = set(all_possible_states())


def payee_and_payer_not_mine():
    return [state for state in _all_possible_states if not state.both_mine]


def payee_not_mine_but_has_record():
    return [
        state
        for state in _all_possible_states
        if not state.is_payee_address_mine
        and state.existing_status_as_payee is not None
    ]


def payer_not_mine_but_has_record():
    return [
        state
        for state in _all_possible_states
        if not state.is_payer_address_mine
        and state.existing_status_as_payer is not None
    ]


def incoming_status_not_pending_and_no_records():
    return [
        state
        for state in _all_possible_states
        if not state.is_incoming_pending and not state.preapproval_exists
    ]


def incoming_pending_for_payee_payer_not_mine():
    return [
        state
        for state in _all_possible_states
        if state.is_incoming_pending
        and state.is_payee_address_mine
        and not state.is_payer_address_mine
    ]


def incoming_pending_non_pending_payee_payer_mine():
    return [
        state
        for state in _all_possible_states
        if state.both_mine
        and state.is_payer_address_mine
        and not state.is_payee_pending
    ]


def incoming_pending_for_non_pending_payer():
    return [
        state
        for state in _all_possible_states
        if state.is_incoming_pending
        and state.is_payer_address_mine
        and not state.is_payer_pending
    ]


def incoming_valid_or_rejected_but_payee_not_pending():
    return [
        state
        for state in _all_possible_states
        if state.is_incoming_valid_or_rejected and not state.is_payee_pending
    ]


# both role are mine, incoming status is 'valid' or 'rejected',
# payee must be 'pending' and payer must be equals to incoming status
def incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming():
    return [
        state
        for state in _all_possible_states
        if state.both_mine
        and state.is_incoming_valid_or_rejected
        and state.is_payee_pending
        and state.existing_status_as_payer != state.incoming_status
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
        state
        for state in _all_possible_states
        if state.both_mine
        and state.is_incoming_closed
        and (
            (not state.is_payee_closed and not state.is_payee_closed)
            or (
                (
                    state.is_payee_closed
                    and not state.is_payee_pending
                    and not state.is_payee_valid
                )
                or (
                    state.is_payee_closed
                    and not state.is_payer_pending
                    and not state.is_payer_valid
                )
            )
        )
    ]


_reduce_role = build_role_reducer()
