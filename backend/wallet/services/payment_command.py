import uuid
from datetime import datetime

import context
from diem import offchain
from wallet import storage
from wallet.services.offchain import _user_kyc_data
from wallet.storage import save_payment_command, models
from wallet.types import TransactionStatus


def add_payment_command(
    account_id,
    reference_id,
    vasp_address,
    merchant_name,
    action,
    currency,
    amount,
    expiration: int,
) -> None:
    payment_command = models.PaymentCommand(
        my_actor_address=context.get().config.vasp_address,
        inbound=True,
        cid=str(uuid.uuid4()),
        reference_id=reference_id,
        sender_address=context.get().config.vasp_address,
        sender_status="none",
        sender_kyc_data=offchain.to_json(_user_kyc_data(account_id)),
        receiver_address=vasp_address,
        receiver_status="none",
        amount=amount,
        currency=currency,
        action=action,
        created_at=datetime.now(),
        status=TransactionStatus.OFF_CHAIN_OUTBOUND,
        account_id=account_id,
        merchant_name=merchant_name,
        expiration=datetime.fromtimestamp(expiration),
    )
    save_payment_command(payment_command)


def update_payment_command_status(reference_id, status):
    storage.update_payment_command_status(reference_id, status)
