import time
from enum import Enum
from typing import List

import context
from diem import offchain, identifier
from diem.offchain import FundPullPreApprovalStatus
from wallet.services import account

# noinspection PyUnresolvedReferences
from wallet.storage.funds_pull_pre_approval_command import (
    models,
    get_account_commands,
    FundsPullPreApprovalCommandNotFound,
    commit_command,
    get_commands_by_sent_status,
    get_command_by_id,
    update_command,
)


class Role(str, Enum):
    PAYEE = "payee"
    PAYER = "payer"


class FundsPullPreApprovalError(Exception):
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
    funds_pull_pre_approval_id, valid_statuses, new_status, operation_name
):
    command = get_command_by_id(funds_pull_pre_approval_id)

    if command:
        if command.status in valid_statuses:
            command.status = new_status
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
):
    commands = get_account_commands(account_id)
    return [preapproval_model_to_command(commands) for commands in commands]


def validate_expiration_timestamp(expiration_timestamp):
    if expiration_timestamp < time.time():
        raise ValueError("expiration timestamp must be in the future")


def process_funds_pull_pre_approvals_requests():
    commands = get_commands_by_sent_status(False)

    for command in commands:
        if command.role == Role.PAYER:
            my_address = command.address
        else:
            my_address = command.biller_address

        cmd = preapproval_model_to_command(my_address=my_address, command=command)

        context.get().offchain_client.send_command(
            cmd, context.get().config.compliance_private_key().sign
        )

        command.offchain_sent = True

        update_command(command)


def preapproval_command_to_model(
    account_id, command: offchain.FundsPullPreApprovalCommand, role: str
) -> models.FundsPullPreApprovalCommand:
    preapproval_object = command.funds_pull_pre_approval
    max_cumulative_amount = preapproval_object.scope.max_cumulative_amount
    max_transaction_amount = preapproval_object.scope.max_transaction_amount

    return models.FundsPullPreApprovalCommand(
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


def preapproval_model_to_command(
    command: models.FundsPullPreApprovalCommand, my_address: str
):
    funds_pull_pre_approval = offchain.FundPullPreApprovalObject(
        funds_pull_pre_approval_id=command.funds_pull_pre_approval_id,
        address=command.address,
        biller_address=command.biller_address,
        scope=offchain.FundPullPreApprovalScopeObject(
            type=offchain.FundPullPreApprovalType.consent,
            expiration_timestamp=command.expiration_timestamp,
            max_cumulative_amount=offchain.ScopedCumulativeAmountObject(
                unit=command.max_cumulative_unit,
                value=command.max_cumulative_unit_value,
                max_amount=offchain.CurrencyObject(
                    amount=command.max_cumulative_amount,
                    currency=command.max_cumulative_amount_currency,
                ),
            ),
            max_transaction_amount=offchain.CurrencyObject(
                amount=command.max_transaction_amount,
                currency=command.max_transaction_amount_currency,
            ),
        ),
        status=command.status,
        description=command.description,
    )

    return offchain.FundsPullPreApprovalCommand(
        my_actor_address=my_address,
        funds_pull_pre_approval=funds_pull_pre_approval,
    )