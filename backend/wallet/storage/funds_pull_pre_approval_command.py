from typing import List

from . import db_session, models


def commit_command(command: models.FundsPullPreApprovalCommand):
    db_session.add(command)
    db_session.commit()


def get_account_commands(account_id: int) -> List[models.FundsPullPreApprovalCommand]:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        account_id=account_id
    ).all()


def get_funds_pull_pre_approval_command(
    funds_pull_pre_approval_id: str,
) -> models.FundsPullPreApprovalCommand:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        funds_pull_pre_approval_id=funds_pull_pre_approval_id
    ).first()


def get_commands_by_type(
    account_id: int, type: str
) -> List[models.FundsPullPreApprovalCommand]:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        account_id=account_id, type=type
    ).all()


def get_commands_by_status(
    account_id: int, status: str
) -> List[models.FundsPullPreApprovalCommand]:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        account_id=account_id, status=status
    ).all()


class FundsPullPreApprovalCommandNotFound(Exception):
    ...


def update_command(
    funds_pull_pre_approval_id: str,
    status: str = None,
    role: str = None,
    offchain_send: bool = False,
) -> models.FundsPullPreApprovalCommand:
    command = models.FundsPullPreApprovalCommand.query.get(funds_pull_pre_approval_id)

    if command:
        if status:
            command.status = status
        if role:
            command.role = role
        command.offchain_send = offchain_send
        commit_command(command)

        return command
    else:
        raise FundsPullPreApprovalCommandNotFound(
            f"Command not found for funds pre approval id {funds_pull_pre_approval_id}"
        )


def update_command_2(command: models.FundsPullPreApprovalCommand):
    command_in_db = models.FundsPullPreApprovalCommand.query.get(
        command.funds_pull_pre_approval_id
    )

    if command_in_db:
        command_in_db.update(command)
        db_session.commit()
    else:
        raise FundsPullPreApprovalCommandNotFound(
            f"Command not found for funds pre approval id {command.funds_pull_pre_approval_id}"
        )


def get_commands_by_role(role: str):
    return models.FundsPullPreApprovalCommand.query.filter_by(role=role).all()


def get_commands_by_send_status(offchain_send: bool):
    return models.FundsPullPreApprovalCommand.query.filter_by(
        offchain_send=offchain_send
    ).all()
