from . import db_session, models


def save_payment(payment: models.Payment):
    db_session.add(payment)
    db_session.commit()

    return payment


def get_payment_details(reference_id: str) -> models.Payment:
    return models.Payment.query.filter_by(reference_id=reference_id).first()
