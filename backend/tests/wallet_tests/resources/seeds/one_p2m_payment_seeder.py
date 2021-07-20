from datetime import datetime

from diem_utils.types.currencies import DiemCurrency
from wallet.services.offchain.p2m_payment import P2MPaymentStatus
from wallet.storage.models import Payment as PaymentModel


class OneP2MPaymentSeeder:
    @staticmethod
    def run(
        db_session, vasp_address, reference_id, action="charge", amount=100_000_000
    ):
        db_session.add(
            PaymentModel(
                vasp_address=vasp_address,
                reference_id=reference_id,
                merchant_name="Bond & Gurki Pet Store",
                action=action,
                currency=DiemCurrency.XUS,
                amount=amount,
                expiration=datetime(2021, 5, 17),
                description="description",
                status=P2MPaymentStatus.READY_FOR_USER,
            )
        )

        db_session.commit()
