from typing import List

from .models import FundsPullPreApprovalCommands

from . import db_session


def commit_command(
    command: FundsPullPreApprovalCommands,
) -> FundsPullPreApprovalCommands:
    db_session.add(command)
    db_session.commit()

    return command


def get_account_commands(account_id: int) -> List[FundsPullPreApprovalCommands]:
    # return [
    #     command
    #     for command in FundsPullPreApprovalCommands.query.filter_by(
    #         account_id=account_id
    #     ).all()
    # ]
    return FundsPullPreApprovalCommands.query.filter_by(account_id=account_id).all()


def get_command(funds_pre_approval_id: str) -> FundsPullPreApprovalCommands:
    return FundsPullPreApprovalCommands.query.filter_by(
        funds_pre_approval_id=funds_pre_approval_id
    ).first()


def get_commands_by_type(
    account_id: int, type: str
) -> List[FundsPullPreApprovalCommands]:
    return FundsPullPreApprovalCommands.query.filter_by(
        account_id=account_id, type=type
    ).all()


def get_commands_by_status(
    account_id: int, status: str
) -> List[FundsPullPreApprovalCommands]:
    return FundsPullPreApprovalCommands.query.filter_by(
        account_id=account_id, status=status
    ).all()


class FundsPullPreApprovalCommandNotFound(Exception):
    ...


def update_command(
    funds_pre_approval_id: str, status: str
) -> FundsPullPreApprovalCommands:
    command = FundsPullPreApprovalCommands.query.get(funds_pre_approval_id)

    if command:
        command.status = status
        commit_command(command)

        return command
    else:
        raise FundsPullPreApprovalCommandNotFound(
            f"Command not found for funds pre approval id {funds_pre_approval_id}"
        )
