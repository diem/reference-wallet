from . import db_session, models


def save_payment_info(payment_info: models.PaymentInfo):
    db_session.add(payment_info)
    db_session.commit()

    return payment_info


def get_payment_info(reference_id: str) -> models.PaymentCommand:
    return models.PaymentInfo.query.filter_by(reference_id=reference_id).first()
