import logging

from wallet.types import TransactionStatus

from . import db_session, models, datetime
from typing import Optional, List, Callable


class PaymentCommandNotFound(Exception):
    ...


def update_status(reference_id: str, new_status):
    command_in_db = get_payment_command(reference_id)

    if command_in_db:
        command_in_db.status = new_status
        command_in_db.update(command_in_db)
        db_session.commit()
    else:
        raise PaymentCommandNotFound(
            f"Command not found for reference id {reference_id}"
        )


def update_payment_command(command: models.PaymentCommand):
    command_in_db = get_payment_command(command.reference_id)

    if command_in_db:
        command_in_db.update(command)
        db_session.commit()
    else:
        raise PaymentCommandNotFound(
            f"Command not found for reference id {command.reference_id}"
        )


def commit_payment_command(command: models.PaymentCommand):
    db_session.add(command)
    db_session.commit()
    return command


def get_payment_command(reference_id: str) -> models.PaymentCommand:
    return models.PaymentCommand.query.filter_by(reference_id=reference_id).first()


def get_commands_by_status(status: TransactionStatus) -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.filter_by(status=status).all()


def get_all() -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.all()


def lock_for_update(
    reference_id: str,
    callback: Callable[[Optional[models.PaymentCommand]], models.PaymentCommand],
) -> models.PaymentCommand:
    try:
        command = (
            models.PaymentCommand.query.filter_by(reference_id=reference_id)
            .populate_existing()
            .with_for_update(nowait=True)
            .one_or_none()
        )
        new_command = callback(command)

        if command:
            update_payment_command(new_command)
        else:
            commit_payment_command(new_command)
    except Exception:
        db_session.rollback()
        raise
    return command
