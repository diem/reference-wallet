from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.storage import models, TransactionStatus


class OneP2PPaymentSeeder:
    @staticmethod
    def run(
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
    ):
        user = OneUser.run(
            db_session,
            account_amount=100_000_000_000,
            account_currency=DiemCurrency.XUS,
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
            currency=DiemCurrency.XUS,
            action=action,
            status=command_status,
            account_id=user.account_id,
        )

        db_session.add(payment_command)
        db_session.commit()
