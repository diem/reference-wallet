#  Copyright (c) The Diem Core Contributors
#  SPDX-License-Identifier: Apache-2.0
import dataclasses
import logging
from datetime import datetime
from operator import attrgetter
from typing import List, Optional

import context
from diem import identifier
import offchain
from offchain import FundPullPreApprovalStatus
from wallet.services.offchain.utils import generate_my_address

from wallet.storage.account import get_account_id_from_subaddr

# noinspection PyUnresolvedReferences
from wallet.storage.funds_pull_pre_approval_command import (
    models,
    get_account_commands,
    commit_command,
    get_commands_by_sent_status,
    get_command_by_id,
    update_command,
    get_account_command_by_id,
    get_account_commands_by_status,
    get_command_by_id_and_role,
    FundsPullPreApprovalCommandNotFound,
)

from .fund_pull_pre_approval_sm import (
    Role,
    reduce_role,
    FundsPullPreApprovalError,
)

logger = logging.getLogger(__name__)


class FundsPullPreApprovalInvalidStatus(FundsPullPreApprovalError):
    ...


@dataclasses.dataclass(frozen=True)
class FPPAObject(offchain.FundsPullPreApprovalCommand):
    biller_name: str = None
    created_timestamp: int = None
    updated_at: int = None
    approved_at: int = None


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
    """Create and approve fund pull pre approval by payer"""
    validate_expiration_timestamp(expiration_timestamp)

    command = get_command_by_id(funds_pull_pre_approval_id)

    if command is not None:
        raise FundsPullPreApprovalError(
            f"Command with id {funds_pull_pre_approval_id} already exist in db"
        )

    address = generate_my_address(account_id)

    commit_command(
        models.FundsPullPreApprovalCommand(
            account_id=account_id,
            address=address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type=funds_pull_pre_approval_type,
            expiration_timestamp=datetime.fromtimestamp(expiration_timestamp),
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
    )


def reject(funds_pull_pre_approval_id):
    update_status(
        funds_pull_pre_approval_id,
        [
            FundPullPreApprovalStatus.pending,
        ],
        FundPullPreApprovalStatus.rejected,
        "reject",
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
    )


def update_status(
    funds_pull_pre_approval_id,
    valid_statuses,
    new_status,
    operation_name,
):
    command = get_command_by_id(funds_pull_pre_approval_id)

    if command:
        if command.status in valid_statuses:
            command.status = new_status
            command.offchain_sent = False

            if operation_name == "approve":
                command.approved_at = datetime.utcnow()

            update_command(command)
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
) -> List[FPPAObject]:
    approvals = [
        preapproval_model_to_command(fppa) for fppa in get_account_commands(account_id)
    ]

    _sort_approvals(approvals)

    return approvals


def _sort_approvals(approvals) -> List[FPPAObject]:
    return approvals.sort(key=attrgetter("created_timestamp"))


def get_funds_pull_pre_approvals_by_status(
    account_id: int,
    status: str,
) -> List[FPPAObject]:
    approvals = [
        preapproval_model_to_command(fppa)
        for fppa in get_account_commands_by_status(account_id, status)
    ]

    _sort_approvals(approvals)

    return approvals


def validate_expiration_timestamp(expiration_timestamp):
    if datetime.fromtimestamp(expiration_timestamp) < datetime.now():
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

        update_command(command)


def preapproval_command_to_model(
    command: offchain.FundsPullPreApprovalCommand,
    role: Role,
    offchain_sent: Optional[bool] = None,
    biller_name: Optional[str] = None,
) -> models.FundsPullPreApprovalCommand:
    account_id = get_account_id_from_command(command, role)
    preapproval_object = command.funds_pull_pre_approval

    max_cumulative_amount = preapproval_object.scope.max_cumulative_amount
    max_transaction_amount = preapproval_object.scope.max_transaction_amount

    model = models.FundsPullPreApprovalCommand(
        account_id=account_id,
        funds_pull_pre_approval_id=preapproval_object.funds_pull_pre_approval_id,
        address=preapproval_object.address,
        biller_address=preapproval_object.biller_address,
        funds_pull_pre_approval_type=preapproval_object.scope.type,
        expiration_timestamp=datetime.fromtimestamp(
            preapproval_object.scope.expiration_timestamp
        ),
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

    if biller_name is not None:
        model.biller_name = biller_name

    return model


def preapproval_model_to_command(
    command: models.FundsPullPreApprovalCommand,
) -> FPPAObject:
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
            expiration_timestamp=int(datetime.timestamp(command.expiration_timestamp)),
            max_cumulative_amount=max_cumulative_amount,
            max_transaction_amount=max_transaction_amount,
        ),
        status=command.status,
        description=command.description,
    )

    return FPPAObject(
        my_actor_address=my_address,
        funds_pull_pre_approval=funds_pull_pre_approval,
        biller_name=command.biller_name,
        created_timestamp=command.created_at,
        updated_at=command.updated_at,
        approved_at=command.approved_at,
        inbound=False,
    )


def get_account_id_from_command(
    command: offchain.FundsPullPreApprovalCommand,
    role: Role,
) -> Optional[int]:
    preapproval = command.funds_pull_pre_approval

    if role == Role.PAYER:
        my_address = preapproval.address
    else:
        my_address = preapproval.biller_address

    _, sub_address = identifier.decode_account(
        my_address, hrp=context.get().config.diem_address_hrp()
    )
    return get_account_id_from_subaddr(sub_address.hex())


def get_command_from_bech32(
    address_bech32: str, funds_pull_pre_approval_id: str
) -> Optional[FPPAObject]:
    address, sub_address = identifier.decode_account(
        address_bech32, context.get().config.diem_address_hrp()
    )
    if address.to_hex() == context.get().config.vasp_address:
        account_id = get_account_id_from_subaddr(sub_address.hex())
        command = get_account_command_by_id(account_id, funds_pull_pre_approval_id)
        if command:
            return preapproval_model_to_command(command)

    return None


def is_my_address(address_bech32: str) -> bool:
    """
    Does the address belong the VASP asking the question?
    """
    hrp = context.get().config.diem_address_hrp()
    address, _ = identifier.decode_account(address_bech32, hrp)

    return address.to_hex() == context.get().config.vasp_address


def handle_fund_pull_pre_approval_command(
    command: offchain.FundsPullPreApprovalCommand,
):
    approval = command.funds_pull_pre_approval
    validate_expiration_timestamp(approval.scope.expiration_timestamp)

    fppa_id = approval.funds_pull_pre_approval_id
    payee_address = approval.biller_address
    payer_address = approval.address

    role = reduce_role(
        incoming_status=approval.status,
        is_payee_address_mine=is_my_address(payee_address),
        is_payer_address_mine=is_my_address(approval.address),
        existing_status_as_payee=get_existing_command_status(payee_address, fppa_id),
        existing_status_as_payer=get_existing_command_status(payer_address, fppa_id),
    )

    command_in_db = get_command_by_id_and_role(
        approval.funds_pull_pre_approval_id, role
    )
    if command_in_db:
        validate_addresses(approval, command_in_db, role)
        validate_status(approval, command_in_db)
        update_command(
            preapproval_command_to_model(command, role),
            approved_at=datetime.utcnow()
            if command.funds_pull_pre_approval.status == FundPullPreApprovalStatus.valid
            else None,
        )
    else:
        biller_name = get_biller_name(command)
        commit_command(
            preapproval_command_to_model(command, role, biller_name=biller_name)
        )


def get_biller_name(command):
    address, _ = identifier.decode_account(
        command.funds_pull_pre_approval.biller_address,
        context.get().config.diem_address_hrp(),
    )
    biller_account = context.get().jsonrpc_client.get_account(address)

    if biller_account:
        return biller_account.role.human_name
    else:
        return None


def get_existing_command_status(address_bech32: str, fppa_id: str) -> Optional[str]:
    """
    Try to find the command in the storage. If found, return its status;
    otherwise return None.
    """
    command = get_command_from_bech32(address_bech32, fppa_id)
    return command and command.funds_pull_pre_approval.status


def validate_status(approval, command_in_db):
    if command_in_db.status == approval.status:
        return

    if command_in_db.status in [
        FundPullPreApprovalStatus.rejected,
        FundPullPreApprovalStatus.closed,
    ]:
        raise FundsPullPreApprovalInvalidStatus


def validate_addresses(approval, command_in_db, role):
    if command_in_db.address is None and role != Role.PAYEE:
        raise FundsPullPreApprovalError("Not payee but address is none")
    if command_in_db.address is not None and approval.address != command_in_db.address:
        raise FundsPullPreApprovalError(
            f"Address is immutable; approval address: {approval.address}, db address: {command_in_db.address}"
        )
    if approval.biller_address != command_in_db.biller_address:
        raise FundsPullPreApprovalError(
            f"Biller address is immutable; approval address: {approval.biller_address}, db address: {command_in_db.biller_address}"
        )
