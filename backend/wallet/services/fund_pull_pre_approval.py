import logging
import time
from enum import Enum
from typing import List, Optional

import context
from diem import offchain, identifier
from diem.offchain import FundPullPreApprovalStatus
from wallet.services import account

# noinspection PyUnresolvedReferences
from wallet.storage import get_account_id_from_subaddr, FundsPullPreApprovalCommandNotFound, get_command_by_id_and_role
from wallet.storage.funds_pull_pre_approval_command import (
    models,
    get_account_commands,
    commit_command,
    get_commands_by_sent_status,
    get_command_by_id,
    update_command,
    get_account_command_by_id,
)
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class Role(str, Enum):
    PAYEE = "payee"
    PAYER = "payer"


class FundsPullPreApprovalError(Exception):
    ...


class FundsPullPreApprovalInvalidStatus(FundsPullPreApprovalError):
    ...


def create_and_approve(
    account_id: int,
    biller_address: str,
    funds_pull_pre_approval_id: str,
    funds_pull_pre_approval_type: str,
    expiration_timestamp: int,
    max_cumulative_unit: str = None,
    max_cumulative_unit_value: int = None,
    max_cumulative_amount: int = None,
    max_cumulative_amount_currency: str = None,
    max_transaction_amount: int = None,
    max_transaction_amount_currency: str = None,
    description: str = None,
) -> None:
    """ Create and approve fund pull pre approval by payer """
    validate_expiration_timestamp(expiration_timestamp)

    command = get_command_by_id(funds_pull_pre_approval_id)

    if command is not None:
        raise FundsPullPreApprovalError(
            f"Command with id {funds_pull_pre_approval_id} already exist in db"
        )

    vasp_address = context.get().config.vasp_address
    sub_address = account.generate_new_subaddress(account_id)
    hrp = context.get().config.diem_address_hrp()
    address = identifier.encode_account(vasp_address, sub_address, hrp)

    commit_command(
        models.FundsPullPreApprovalCommand(
            account_id=account_id,
            address=address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type=funds_pull_pre_approval_type,
            expiration_timestamp=expiration_timestamp,
            max_cumulative_unit=max_cumulative_unit,
            max_cumulative_unit_value=max_cumulative_unit_value,
            max_cumulative_amount=max_cumulative_amount,
            max_cumulative_amount_currency=max_cumulative_amount_currency,
            max_transaction_amount=max_transaction_amount,
            max_transaction_amount_currency=max_transaction_amount_currency,
            description=description,
            status=FundPullPreApprovalStatus.valid,
            role=Role.PAYER,
        )
    )


def approve(funds_pull_pre_approval_id: str) -> None:
    update_status(
        funds_pull_pre_approval_id,
        [
            FundPullPreApprovalStatus.pending,
        ],
        FundPullPreApprovalStatus.valid,
        "approve",
        should_send=True,
    )


def reject(funds_pull_pre_approval_id):
    update_status(
        funds_pull_pre_approval_id,
        [
            FundPullPreApprovalStatus.pending,
        ],
        FundPullPreApprovalStatus.rejected,
        "reject",
        should_send=True,
    )


def close(funds_pull_pre_approval_id):
    update_status(
        funds_pull_pre_approval_id,
        [
            FundPullPreApprovalStatus.pending,
            FundPullPreApprovalStatus.valid,
        ],
        FundPullPreApprovalStatus.closed,
        "close",
        should_send=True,
    )


def update_status(
    funds_pull_pre_approval_id,
    valid_statuses,
    new_status,
    operation_name,
    should_send=False,
):
    command = get_command_by_id(funds_pull_pre_approval_id)

    if command:
        if command.status in valid_statuses:
            command.status = new_status
            command.offchain_sent = not should_send
            update_command(command.account_id, command)
        else:
            raise FundsPullPreApprovalError(
                f"Could not {operation_name} command with status {command.status}"
            )
    else:
        raise FundsPullPreApprovalError(
            f"Could not find command {funds_pull_pre_approval_id}"
        )


def get_funds_pull_pre_approvals(
    account_id: int,
) -> List[offchain.FundsPullPreApprovalCommand]:
    return [
        preapproval_model_to_command(fppa) for fppa in get_account_commands(account_id)
    ]


def validate_expiration_timestamp(expiration_timestamp):
    if expiration_timestamp < time.time():
        raise ValueError("expiration timestamp must be in the future")


def process_funds_pull_pre_approvals_requests():
    commands = get_commands_by_sent_status(False)

    for command in commands:
        cmd = preapproval_model_to_command(command)

        logger.info(
            f"Outgoing pre-approval: "
            f"ID={cmd.funds_pull_pre_approval.funds_pull_pre_approval_id} "
            f"status={cmd.funds_pull_pre_approval.status} "
            f"my_address={cmd.my_address()} "
            f"opponent_address={cmd.opponent_address()} "
            f"payer={cmd.funds_pull_pre_approval.address} "
            f"payee={cmd.funds_pull_pre_approval.biller_address}"
        )

        context.get().offchain_client.send_command(
            cmd, context.get().config.compliance_private_key().sign
        )

        command.offchain_sent = True

        update_command(command.account_id, command)


def preapproval_command_to_model(
    account_id,
    command: offchain.FundsPullPreApprovalCommand,
    role: str,
    offchain_sent: Optional[bool] = None,
) -> models.FundsPullPreApprovalCommand:
    preapproval_object = command.funds_pull_pre_approval
    max_cumulative_amount = preapproval_object.scope.max_cumulative_amount
    max_transaction_amount = preapproval_object.scope.max_transaction_amount

    model = models.FundsPullPreApprovalCommand(
        account_id=account_id,
        funds_pull_pre_approval_id=preapproval_object.funds_pull_pre_approval_id,
        address=preapproval_object.address,
        biller_address=preapproval_object.biller_address,
        funds_pull_pre_approval_type=preapproval_object.scope.type,
        expiration_timestamp=preapproval_object.scope.expiration_timestamp,
        max_cumulative_unit=max_cumulative_amount.unit
        if max_cumulative_amount
        else None,
        max_cumulative_unit_value=max_cumulative_amount.value
        if max_cumulative_amount
        else None,
        max_cumulative_amount=max_cumulative_amount.max_amount.amount
        if max_cumulative_amount
        else None,
        max_cumulative_amount_currency=max_cumulative_amount.max_amount.currency
        if max_cumulative_amount
        else None,
        max_transaction_amount=max_transaction_amount.amount
        if max_transaction_amount
        else None,
        max_transaction_amount_currency=max_transaction_amount.currency
        if max_transaction_amount
        else None,
        description=preapproval_object.description,
        status=preapproval_object.status,
        role=role,
    )

    if offchain_sent is not None:
        model.offchain_sent = offchain_sent

    return model


def preapproval_model_to_command(
    command: models.FundsPullPreApprovalCommand,
) -> offchain.FundsPullPreApprovalCommand:
    if command.role == Role.PAYER:
        my_address = command.address
    else:
        my_address = command.biller_address

    max_cumulative_amount = None
    if command.max_cumulative_unit is not None:
        max_cumulative_amount = offchain.ScopedCumulativeAmountObject(
            unit=command.max_cumulative_unit,
            value=command.max_cumulative_unit_value,
            max_amount=offchain.CurrencyObject(
                amount=command.max_cumulative_amount,
                currency=command.max_cumulative_amount_currency,
            ),
        )

    max_transaction_amount = None
    if command.max_transaction_amount is not None:
        max_transaction_amount = offchain.CurrencyObject(
            amount=command.max_transaction_amount,
            currency=command.max_transaction_amount_currency,
        )

    funds_pull_pre_approval = offchain.FundPullPreApprovalObject(
        funds_pull_pre_approval_id=command.funds_pull_pre_approval_id,
        address=command.address,
        biller_address=command.biller_address,
        scope=offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=command.expiration_timestamp,
            max_cumulative_amount=max_cumulative_amount,
            max_transaction_amount=max_transaction_amount,
        ),
        status=command.status,
        description=command.description,
    )

    return offchain.FundsPullPreApprovalCommand(
        my_actor_address=my_address,
        funds_pull_pre_approval=funds_pull_pre_approval,
    )


def get_command_from_bech32(
    address_bech32: str, funds_pull_pre_approval_id: str
) -> Optional[models.FundsPullPreApprovalCommand]:
    address, sub_address = identifier.decode_account(
        address_bech32, context.get().config.diem_address_hrp()
    )
    if address.to_hex() == context.get().config.vasp_address:
        account_id = get_account_id_from_subaddr(sub_address.hex())
        command = get_account_command_by_id(account_id, funds_pull_pre_approval_id)
        if command:
            return preapproval_model_to_command(command, address_bech32)

    return None


@dataclass(frozen=True)
class Combination:
    incoming_status: str  # 4
    is_payee_address_mine: bool  # 2
    is_payer_address_mine: bool  # 2
    existing_status_as_payee: Optional[str]  # 5
    existing_status_as_payer: Optional[str]  # 5


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


def get_role(approval):
    hrp = context.get().config.diem_address_hrp()
    biller_address, biller_sub_address = identifier.decode_account(
        approval.biller_address, hrp
    )
    address, sub_address = identifier.decode_account(approval.address, hrp)
    payee_command = get_command_from_bech32(
        approval.biller_address, approval.funds_pull_pre_approval_id
    )
    payer_command = get_command_from_bech32(
        approval.address, approval.funds_pull_pre_approval_id
    )

    combination = Combination(
        incoming_status=approval.status,
        is_payee_address_mine=is_my_address(biller_address),
        is_payer_address_mine=is_my_address(address),
        existing_status_as_payee=payee_command.funds_pull_pre_approval.status
        if payee_command is not None
        else None,
        existing_status_as_payer=payer_command.funds_pull_pre_approval.status
        if payer_command is not None
        else None,
    )

    combinations = get_combinations()

    role = combinations.get(combination)

    print(f"combination: {combination}, role: {role}")

    if role is None:
        raise FundsPullPreApprovalError()

    return role


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
        combination for combination in all_combinations() if both_not_mine(combination)
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
        if incoming_status_is_not_pending(combination) and both_no_records(combination)
    ]


def incoming_pending_for_payee():
    # if incoming status is 'pending', the payer address is not mine
    # and the payee address is mine all combinations are invalid
    return [
        combination
        for combination in all_combinations()
        if not combination.is_payer_address_mine
        and combination.is_payee_address_mine
        and incoming_status_is_pending(combination)
    ]


def incoming_valid_or_rejected_but_payee_not_pending():
    return [
        combination
        for combination in all_combinations()
        if incoming_status_is_valid_or_rejected(combination)
        and payee_status_is_not_pending(combination)
    ]


# both role are mine, incoming status is 'valid' or 'rejected',
# payee must be 'pending' and payer must be equals to incoming status
def incoming_valid_or_rejected_my_payee_not_pending_and_my_payer_not_equal_to_incoming():
    return [
        combination
        for combination in all_combinations()
        if both_mine(combination)
        and incoming_status_is_valid_or_rejected(combination)
        and payee_status_is_pending(combination)
        and payer_status_equal_incoming_status(combination)
    ]


def incoming_status_is_valid_or_rejected(combination):
    return combination.incoming_status in [
        FundPullPreApprovalStatus.valid,
        FundPullPreApprovalStatus.rejected,
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
        if both_mine(combination)
        and (
            payee_status_is_not_pending(combination)
            or (
                payee_status_is_pending(combination)
                and payer_status_is_not_pending(combination)
                and payer_status_is_not_none(combination)
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
        if both_mine(combination)
        and incoming_status_is_closed(combination)
        and (
            (
                payer_status_is_not_closed(combination)
                and payee_status_is_not_closed(combination)
            )
            or (
                (
                    payer_status_is_closed(combination)
                    and payee_status_is_not_pending_or_valid(combination)
                )
                or (
                    payee_status_is_closed(combination)
                    and payer_status_is_not_pending_or_valid
                )
            )
        )
    ]


def payee_status_is_closed(combination):
    return combination.existing_status_as_payee is FundPullPreApprovalStatus.closed


def payer_status_is_closed(combination):
    return combination.existing_status_as_payer is FundPullPreApprovalStatus.closed


def payee_status_is_not_pending_or_valid(combination):
    return combination.existing_status_as_payee not in [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
    ]


def payer_status_is_not_pending_or_valid(combination):
    return combination.existing_status_as_payer not in [
        FundPullPreApprovalStatus.pending,
        FundPullPreApprovalStatus.valid,
    ]


def both_not_mine(combination):
    return (
        not combination.is_payee_address_mine and not combination.is_payer_address_mine
    )


def both_no_records(combination):
    return (
        combination.existing_status_as_payer is None
        and combination.existing_status_as_payee is None
    )


def payee_status_is_not_closed(combination):
    return combination.existing_status_as_payee is not FundPullPreApprovalStatus.closed


def payer_status_is_not_closed(combination):
    return combination.existing_status_as_payer is not FundPullPreApprovalStatus.closed


def incoming_status_is_not_pending(combination):
    return combination.incoming_status is not FundPullPreApprovalStatus.pending


def payer_status_equal_incoming_status(combination):
    return combination.existing_status_as_payer != combination.incoming_status


def payer_status_is_not_none(combination):
    return combination.existing_status_as_payer is not None


def payer_status_is_not_pending(combination):
    return combination.existing_status_as_payer is not FundPullPreApprovalStatus.pending


def payee_status_is_not_pending(combination):
    return combination.existing_status_as_payee is not FundPullPreApprovalStatus.pending


def payee_status_is_pending(combination):
    return combination.existing_status_as_payee is FundPullPreApprovalStatus.pending


def incoming_status_is_pending(combination):
    return combination.incoming_status is FundPullPreApprovalStatus.pending


def incoming_status_is_closed(combination):
    return combination.incoming_status is FundPullPreApprovalStatus.closed


def both_mine(combination):
    return combination.is_payer_address_mine and combination.is_payee_address_mine


def make_error_combinations(combinations) -> dict:
    return {combination: None for combination in combinations}


def is_my_address(address):
    return address.to_hex() == context.get().config.vasp_address


def handle_fund_pull_pre_approval_command(command):
    approval = command.funds_pull_pre_approval
    validate_expiration_timestamp(approval.scope.expiration_timestamp)
    role = get_role(approval)
    command_in_db = get_command_by_id_and_role(
        approval.funds_pull_pre_approval_id, role
    )
    if command_in_db:
        validate_addresses(approval, command_in_db)
        validate_status(approval, command_in_db)

    hrp = context.get().config.diem_address_hrp()

    if role == Role.PAYER:
        if approval.status == FundPullPreApprovalStatus.pending:
            if command_in_db:
                update_command(
                    command_in_db.account_id,
                    preapproval_command_to_model(
                        account_id=command_in_db.account_id,
                        command=command,
                        role=command_in_db.role,
                    ),
                )
            else:
                address, sub_address = identifier.decode_account(approval.address, hrp)

                commit_command(
                    preapproval_command_to_model(
                        account_id=get_account_id_from_subaddr(sub_address.hex()),
                        command=command,
                        role=Role.PAYER,
                    )
                )
        if approval.status in [
            FundPullPreApprovalStatus.valid,
            FundPullPreApprovalStatus.rejected,
        ]:
            raise FundsPullPreApprovalInvalidStatus()
        if approval.status == FundPullPreApprovalStatus.closed:
            if command_in_db:
                update_command(
                    command_in_db.account_id,
                    preapproval_command_to_model(
                        account_id=command_in_db.account_id,
                        command=command,
                        role=command_in_db.role,
                    ),
                )
            else:
                raise FundsPullPreApprovalCommandNotFound()
    elif role == Role.PAYEE:
        if approval.status in [
            FundPullPreApprovalStatus.valid,
            FundPullPreApprovalStatus.rejected,
        ]:
            if command_in_db:
                if command_in_db.status == FundPullPreApprovalStatus.pending:
                    (
                        biller_address,
                        biller_sub_address,
                    ) = identifier.decode_account(approval.biller_address, hrp)

                    update_command(
                        command_in_db.account_id,
                        preapproval_command_to_model(
                            account_id=get_account_id_from_subaddr(
                                biller_sub_address.hex()
                            ),
                            command=command,
                            role=command_in_db.role,
                        ),
                    )
                else:
                    raise FundsPullPreApprovalInvalidStatus()
            else:
                raise FundsPullPreApprovalCommandNotFound()
        if approval.status == FundPullPreApprovalStatus.closed:
            if command_in_db:
                update_command(
                    command_in_db.account_id,
                    preapproval_command_to_model(
                        account_id=command_in_db.account_id,
                        command=command,
                        role=command_in_db.role,
                    ),
                )
            else:
                raise FundsPullPreApprovalCommandNotFound()
        if approval.status == FundPullPreApprovalStatus.pending:
            raise FundsPullPreApprovalInvalidStatus()


def validate_status(approval, command_in_db):
    if command_in_db.status in [
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ]:
        raise FundsPullPreApprovalInvalidStatus
    if (
        command_in_db.status == approval.status
        and command_in_db.status != FundPullPreApprovalStatus.pending
    ):
        raise FundsPullPreApprovalInvalidStatus


def validate_addresses(approval, command_in_db):
    if (
        approval.address != command_in_db.address
        or approval.biller_address != command_in_db.biller_address
    ):
        raise ValueError("address and biller_addres values are immutable")