import logging

from wallet.types import TransactionStatus

from . import db_session, models
from typing import Optional, List, Callable


class PaymentCommandNotFound(Exception):
    ...


def save_payment_command(command: models.PaymentCommand):
    db_session.add(command)
    db_session.commit()
    return command


def get_payment_command(reference_id: str) -> models.PaymentCommand:
    return models.PaymentCommand.query.filter_by(reference_id=reference_id).first()


def get_payment_commands_by_status(
    status: TransactionStatus,
) -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.filter_by(status=status).all()


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
        save_payment_command(model)
    except Exception:
        db_session.rollback()
        raise
    return model


def get_account_payment_commands(account_id) -> List[models.PaymentCommand]:
    return models.PaymentCommand.query.filter_by(account_id=account_id).all()
