from typing import List

from .models import FundsPullPreApprovalCommands

from . import db_session


def commit_command(
    command: FundsPullPreApprovalCommands,
) -> FundsPullPreApprovalCommands:
    db_session.add(command)
    db_session.commit()

    return command


def get_command(funds_pre_approval_id: str) -> FundsPullPreApprovalCommands:
    return FundsPullPreApprovalCommands.query.filter_by(
        funds_pre_approval_id=funds_pre_approval_id
    ).first()


def get_commands_by_type(status: str) -> List[FundsPullPreApprovalCommands]:
    return FundsPullPreApprovalCommands.query.filter_by(status=status).all()
