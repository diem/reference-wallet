from datetime import datetime

from diem_utils.types.currencies import DiemCurrency
from wallet.storage.models import Payment as PaymentModel


class OnePaymentSeeder:
    @staticmethod
    def run(db_session, vasp_address, reference_id, action="charge"):
        db_session.add(
            PaymentModel(
                vasp_address=vasp_address,
                reference_id=reference_id,
                merchant_name="Bond & Gurki Pet Store",
                action=action,
                currency=DiemCurrency.XUS,
                amount=100_000_000,
                expiration=datetime(2021, 5, 17),
                description="description",
            )
        )

        db_session.commit()
