import uuid

from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.storage import models, TransactionStatus
from datetime import datetime


class PaymentCommandSeeder:
    @staticmethod
    def run_full_command(
        db_session,
        reference_id,
        amount,
        sender_address,
        sender_status,
        receiver_address,
        receiver_status,
        action,
        is_sender,
        command_status=TransactionStatus.PENDING,
        currency=DiemCurrency.XUS,
        expiration=datetime.fromtimestamp(1802010490),
        merchant_name="Gurki's Dog House",
    ):
        user = OneUser.run(
            db_session,
            account_amount=100_000_000_000,
            account_currency=currency,
        )

        my_actor_address = sender_address if is_sender else receiver_address

        payment_command = models.PaymentCommand(
            my_actor_address=my_actor_address,
            inbound=True,
            cid=reference_id,
            reference_id=reference_id,
            sender_address=sender_address,
            sender_status=sender_status,
            receiver_address=receiver_address,
            receiver_status=receiver_status,
            amount=amount,
            currency=currency,
            action=action,
            status=command_status,
            account_id=user.account_id,
            expiration=expiration,
            merchant_name=merchant_name,
        )

        db_session.add(payment_command)
        db_session.commit()

    @staticmethod
    def run_minimal_command(
        db_session,
        reference_id,
        receiver_address,
    ):
        user = OneUser.run(
            db_session,
            account_amount=100_000_000_000,
            account_currency=DiemCurrency.XUS,
        )

        my_actor_address = "tdm1pzmhcxpnyns7m035ctdqmexxad8ptgazxhllvyscesqdgp"

        payment_command = models.PaymentCommand(
            my_actor_address=my_actor_address,
            inbound=False,
            cid=reference_id,
            reference_id=reference_id,
            sender_address=my_actor_address,
            sender_status="none",
            receiver_address=receiver_address,
            receiver_status="none",
            amount=None,
            currency=None,
            action="charge",
            status=TransactionStatus.WAIT_FOR_INFO,
            account_id=user.account_id,
            expiration=None,
            merchant_name=None,
        )

        db_session.add(payment_command)
        db_session.commit()
