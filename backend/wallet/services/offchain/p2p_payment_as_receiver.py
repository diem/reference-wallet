import logging

import offchain
from offchain import Status
from wallet import storage
from wallet.services.offchain import p2p_payment as pc_service
from wallet.types import TransactionStatus

logger = logging.getLogger(__name__)


def save_payment_command_as_receiver(payment_command: offchain.PaymentCommand):
    sender_status = payment_command.payment.sender.status.status
    reference_id = payment_command.reference_id()
    logger.info(f"save payment command as receiver for reference_id: {reference_id}.")

    if sender_status == Status.needs_kyc_data:
        storage.save_payment_command(
            pc_service.payment_command_to_model(
                payment_command, TransactionStatus.OFF_CHAIN_RECEIVER_OUTBOUND
            )
        )
    elif sender_status == Status.ready_for_settlement:
        model = storage.get_payment_command(reference_id)

        if model:
            model.status = TransactionStatus.OFF_CHAIN_READY
            storage.save_payment_command(model)
        else:
            logger.warning(
                f"Failed to find payment command in DB for reference_id {reference_id}."
            )
    elif sender_status == Status.abort:
        model = storage.get_payment_command(reference_id)

        if model:
            model.status = TransactionStatus.CANCELED
            storage.save_payment_command(model)
    else:
        logger.warning(
            f"Unhandled sender status '{sender_status}' received for reference id {reference_id}"
        )
