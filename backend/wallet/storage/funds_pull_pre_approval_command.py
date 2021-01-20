from typing import List

from . import db_session, models


def commit_command(command: models.FundsPullPreApprovalCommand):
    db_session.add(command)
    db_session.commit()


def get_account_commands(account_id: int) -> List[models.FundsPullPreApprovalCommand]:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        account_id=account_id
    ).all()


def get_account_command_by_id(account_id: int, funds_pull_pre_approval_id: str):
    return models.FundsPullPreApprovalCommand.query.filter_by(
        account_id=account_id, funds_pull_pre_approval_id=funds_pull_pre_approval_id
    ).first()


def get_command_by_id(
    funds_pull_pre_approval_id: str,
) -> models.FundsPullPreApprovalCommand:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        funds_pull_pre_approval_id=funds_pull_pre_approval_id
    ).first()


def get_command_by_id_and_role(
    funds_pull_pre_approval_id: str, role: str
) -> models.FundsPullPreApprovalCommand:
    return models.FundsPullPreApprovalCommand.query.filter_by(
        funds_pull_pre_approval_id=funds_pull_pre_approval_id, role=role
    ).first()


class FundsPullPreApprovalCommandNotFound(Exception):
    ...


def update_command(account_id: int, command: models.FundsPullPreApprovalCommand):
    command_in_db = get_account_command_by_id(
        account_id, command.funds_pull_pre_approval_id
    )

    if command_in_db:
        command_in_db.update(command)
        db_session.commit()
    else:
        raise FundsPullPreApprovalCommandNotFound(
            f"Command not found for funds pre approval id {command.funds_pull_pre_approval_id}"
        )


def get_commands_by_sent_status(offchain_sent: bool):
    return models.FundsPullPreApprovalCommand.query.filter_by(
        offchain_sent=offchain_sent
    ).all()
