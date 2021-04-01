#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from offchain import FundPullPreApprovalStatus

logger = logging.getLogger(__name__)


class FundsPullPreApprovalError(Exception):
    ...


class FundsPullPreApprovalStateError(Exception):
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

    def __str__(self):
        return (
            f"incoming_status={self.incoming_status}, "
            f"is_payee_address_mine={self.is_payee_address_mine}, "
            f"is_payer_address_mine={self.is_payer_address_mine}, "
            f"existing_status_as_payee={self.existing_status_as_payee}, "
            f"existing_status_as_payer={self.existing_status_as_payer}"
        )

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
    def is_incoming_valid(self) -> bool:
        return self.incoming_status is FundPullPreApprovalStatus.valid

    @property
    def is_incoming_rejected(self) -> bool:
        return self.incoming_status is FundPullPreApprovalStatus.rejected

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
    def is_payee_rejected(self):
        return self.existing_status_as_payee is FundPullPreApprovalStatus.rejected

    @property
    def is_payer_pending(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.pending

    @property
    def is_payer_closed(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.closed

    @property
    def is_payer_valid(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.valid

    @property
    def is_payer_rejected(self):
        return self.existing_status_as_payer is FundPullPreApprovalStatus.rejected


def build_role_reducer():
    Incoming = FundPullPreApprovalStatus
    Existing = FundPullPreApprovalStatus

    # fmt: off
    explicit_states = {
        # New request from a peyee in the same VASP
        FppaState(Incoming.pending, True, True, Existing.pending, None): Role.PAYER,
        # Payee in the same VASP updates an existing request
        FppaState(Incoming.pending, True, True, Existing.pending, Existing.pending): Role.PAYER,
        # New request from another VASP
        FppaState(Incoming.pending, False, True, None, None): Role.PAYER,
        # Updated request from another VASP
        FppaState(Incoming.pending, False, True, None, Existing.pending): Role.PAYER,
        # Payer from another VASP approves
        FppaState(Incoming.valid, True, False, Existing.pending, None): Role.PAYEE,
        FppaState(Incoming.valid, True, False, Existing.valid, None): Role.PAYEE,
        # Payer from the same VASP approves
        FppaState(Incoming.valid, True, True, Existing.pending, Existing.valid): Role.PAYEE,
        FppaState(Incoming.valid, True, True, Existing.valid, Existing.valid): Role.PAYEE,
        # Payer from another VASP rejects
        FppaState(Incoming.rejected, True, False, Existing.pending, None): Role.PAYEE,
        FppaState(Incoming.rejected, True, False, Existing.rejected, None): Role.PAYEE,
        # Payer from the same VASP rejects
        FppaState(Incoming.rejected, True, True, Existing.pending, Existing.rejected): Role.PAYEE,
        FppaState(Incoming.rejected, True, True, Existing.rejected, Existing.rejected): Role.PAYEE,
        # Payee from another VASP closes a pending request
        FppaState(Incoming.closed, False, True, None, Existing.pending): Role.PAYER,
        # Payee from another VASP closes again
        FppaState(Incoming.closed, False, True, None, Existing.closed): Role.PAYER,
        # Payee from another VASP closes a valid request
        FppaState(Incoming.closed, False, True, None, Existing.valid): Role.PAYER,
        # Payee from the same VASP closes a pending request
        FppaState(Incoming.closed, True, True, Existing.closed, Existing.pending): Role.PAYER,
        # Payee from the same VASP closes a valid request
        FppaState(Incoming.closed, True, True, Existing.closed, Existing.valid): Role.PAYER,
        # Payer from another VASP closes a pending request
        FppaState(Incoming.closed, True, False, Existing.pending, None): Role.PAYEE,
        # Payer from another VASP closes again
        FppaState(Incoming.closed, True, False, Existing.closed, None): Role.PAYEE,
        # Payer from another VASP closes a valid request
        FppaState(Incoming.closed, True, False, Existing.valid, None): Role.PAYEE,
        # Payer from the same VASP closes a pending request
        FppaState(Incoming.closed, True, True, Existing.pending, Existing.closed): Role.PAYEE,
        # Payer from the same VASP closes a valid request
        FppaState(Incoming.closed, True, True, Existing.valid, Existing.closed): Role.PAYEE,
        # Payer closes again
        FppaState(Incoming.closed, True, True, Existing.closed, Existing.closed): Role.PAYEE,
    }

    all_states = {}

    all_states.update(make_error_states(
        payee_and_payer_not_mine(),
        "Bad request: Both the payee and the payer do not belong to this VASP"
    ))
    all_states.update(make_error_states(
        payee_not_mine_but_has_record(),
        "Payee doesn't belong to this VASP but the request is in the storage"
    ))
    all_states.update(make_error_states(
        payer_not_mine_but_has_record(),
        "Payer doesn't belong to this VASP but the request is in the storage"
    ))
    all_states.update(make_error_states(
        incoming_status_not_pending_and_no_records(),
        "Incoming update for unknown request "
    ))
    all_states.update(make_error_states(
        incoming_pending_for_payee_payer_not_mine(),
        "Payee cannot update request status to pending"
    ))
    all_states.update(make_error_states(
        incoming_pending_for_non_pending_payer(),
        "Processed request cannot become pending"
    ))
    all_states.update(make_error_states(
        incoming_pending_both_mine_payee_non_pending(),
        "Payee is not pending but a request claims it is"
    ))
    all_states.update(make_error_states(
        incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming(),
        "Only pending requests can become valid or rejected"
    ))
    all_states.update(make_error_states(
        invalid_states_for_incoming_closed(),
        "Only pending and valid requests can be closed"
    ))
    all_states.update(make_error_states(
        payee_valid_or_closed_becomes_rejected(),
        "Approved or closed request cannot be rejected"
    ))
    all_states.update(make_error_states(
        payee_rejected_or_closed_becomes_valid(),
        "Rejected or closed request cannot be approved"
    ))
    all_states.update(make_error_states(
        payee_approves_or_rejects(),
        "Payee cannot approve or reject"
    ))
    all_states.update(make_error_states(
        rejected_being_closed(),
        "Cannot close rejected request"
    ))

    all_states.update(explicit_states)
    # fmt: on

    def reducer(state: FppaState) -> Role:
        x = all_states[state]

        if isinstance(x, FundsPullPreApprovalStateError):
            raise x

        return x

    return reducer


def make_error_states(states, error_description) -> dict:
    return {st: FundsPullPreApprovalStateError(error_description) for st in states}


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
    return [
        state
        for state in _all_possible_states
        if not state.is_payer_address_mine and not state.is_payee_address_mine
    ]


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


def payee_valid_or_closed_becomes_rejected():
    return [
        state
        for state in _all_possible_states
        if not state.is_payer_address_mine
        and state.is_payee_address_mine
        and (state.is_payee_valid or state.is_payee_closed)
        and state.is_incoming_rejected
    ]


def payee_rejected_or_closed_becomes_valid():
    return [
        state
        for state in _all_possible_states
        if not state.is_payer_address_mine
        and state.is_payee_address_mine
        and (state.is_payee_rejected or state.is_payee_closed)
        and state.is_incoming_valid
    ]


def payee_approves_or_rejects():
    return [
        state
        for state in _all_possible_states
        if state.is_payer_address_mine
        and not state.is_payee_address_mine
        and (state.is_incoming_valid or state.is_incoming_rejected)
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


def incoming_pending_both_mine_payee_non_pending():
    return [
        state
        for state in _all_possible_states
        if state.both_mine and not state.is_payee_pending
    ]


def incoming_pending_for_non_pending_payer():
    return [
        state
        for state in _all_possible_states
        if state.is_incoming_pending
        and state.is_payer_address_mine
        and not state.is_payer_pending
    ]


def incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming():
    return [
        state
        for state in _all_possible_states
        if state.both_mine
        and state.is_incoming_valid_or_rejected
        and state.is_payee_pending
        and state.existing_status_as_payer != state.incoming_status
    ]


def rejected_being_closed():
    return [
        state
        for state in _all_possible_states
        if not state.both_mine
        and state.is_incoming_closed
        and (state.is_payee_rejected or state.is_payer_rejected)
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
