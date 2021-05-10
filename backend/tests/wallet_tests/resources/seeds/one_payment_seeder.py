from datetime import datetime

from diem_utils.types.currencies import DiemCurrency
from wallet.storage.models import Payment as PaymentModel


class OnePaymentSeeder:
    @staticmethod
    def run(db_session, vasp_address, reference_id):
        db_session.add(
            PaymentModel(
                vasp_address=vasp_address,
                reference_id=reference_id,
                merchant_name="Bond & Gurki Pet Store",
                merchant_legal_name="Bond & Gurki Pet Store",
                city="Dogcity",
                country="Dogland",
                line1="1234 Puppy Street",
                line2="dogpalace 3",
                postal_code="123456",
                state="Dogstate",
                action="charge",
                currency=DiemCurrency.XUS,
                amount=100_000_000,
                expiration=datetime(2021, 5, 17),
                description="description",
            )
        )

        db_session.commit()
