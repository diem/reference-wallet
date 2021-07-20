import logging

from . import db_session, models

logger = logging.getLogger(__name__)


def save_payment(payment: models.Payment):
    db_session.add(payment)
    db_session.commit()

    return payment


def get_payment_details(reference_id: str) -> models.Payment:
    return models.Payment.query.filter_by(reference_id=reference_id).first()


def update_payment(reference_id: str, status: str, recipient_signature: str = None):
    payment_in_db = get_payment_details(reference_id)

    if recipient_signature:
        payment_in_db.recipient_signature = recipient_signature

    payment_in_db.status = status

    try:
        payment_in_db.update(payment_in_db)
        db_session.commit()
    except Exception as e:
        logger.error(error)
        raise error
