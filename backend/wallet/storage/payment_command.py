import logging

from wallet.types import TransactionStatus

from . import db_session, models
from typing import Optional, List, Callable


class PaymentCommandNotFound(Exception):
    ...


def update_payment_command(command: models.PaymentCommand):
    command_in_db = get_payment_command(command.reference_id)

    if command_in_db:
        command_in_db.update(command)
        db_session.commit()
    else:
        raise PaymentCommandNotFound(
            f"Command not found for reference id {command.reference_id}"
        )

    return command_in_db


def commit_payment_command(command: models.PaymentCommand):
    db_session.add(command)
    db_session.commit()
    return command


def get_payment_command(reference_id: str) -> models.PaymentCommand:
    return models.PaymentCommand.query.filter_by(reference_id=reference_id).first()


def get_payment_commands_by_status(
    status: TransactionStatus,
) -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.filter_by(status=status).all()


def get_all() -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.all()


def lock_for_update(
    reference_id: str,
    callback: Callable[[Optional[models.PaymentCommand]], models.PaymentCommand],
) -> models.PaymentCommand:
    try:
        model = (
            models.PaymentCommand.query.filter_by(reference_id=reference_id)
            .populate_existing()
            .with_for_update(nowait=True)
            .one_or_none()
        )
        model = callback(model)
        commit_payment_command(model)
    except Exception:
        db_session.rollback()
        raise
    return model


def get_account_payment_commands(account_id) -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.filter_by(account_id=account_id).all()
