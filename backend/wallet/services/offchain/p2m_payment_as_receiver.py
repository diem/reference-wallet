import typing
from datetime import datetime

from diem import txnmetadata
from offchain import CommandRequestObject, GetPaymentInfo
from offchain.types import (
    GetInfoCommandResponse,
    InitChargePaymentResponse,
    PaymentInfoObject,
)
from wallet import storage
from wallet.services.offchain import utils
from wallet.services.offchain.p2m_payment import (
    P2MPaymentStatus,
    P2MPaymentNotFoundError,
)


def handle_incoming_get_payment_info_request(request: CommandRequestObject):
    # The get_payment_info command arrive only when DRW playing the Merchant\Receiver
    # role in the communication, and therefore we can assume that the relevant payment
    # already been saved in DB and all other data we should return we can mock
    get_info_command_object = typing.cast(GetPaymentInfo, request.command)

    reference_id = get_info_command_object.reference_id

    payment_model = storage.get_payment_details(reference_id)

    payment_info_object = PaymentInfoObject.new_payment_info_object(
        reference_id=reference_id,
        receiver_address=payment_model.vasp_address,
        name=payment_model.merchant_name,
        legal_name=payment_model.merchant_name,
        city="Dogcity",
        country="DL",
        line1="1234 Puppy Street",
        line2="dogpalace",
        postal_code="123456",
        state="Dogstate",
        amount=payment_model.amount,
        currency=payment_model.currency,
        action=payment_model.action,
        timestamp=int(datetime.timestamp(payment_model.created_at)),
        valid_until=int(datetime.timestamp(payment_model.expiration))
        if payment_model.action == "auth"
        else None,
        description=payment_model.description,
    )

    return utils.jws_response(
        reference_id,
        result_object=GetInfoCommandResponse(payment_info=payment_info_object),
    )


def handle_init_charge_command(request: CommandRequestObject):
    reference_id = request.command.reference_id

    payment_model = storage.get_payment_details(reference_id)

    if not payment_model:
        raise P2MPaymentNotFoundError(f"Could not find payment {reference_id}")

    payment_amount = payment_model.amount

    if payment_amount > 1_000_000_000:
        recipient_signature = sign_as_receiver(
            reference_id=reference_id,
            sender_address=request.command.sender.account_address,
            amount=payment_amount,
        )

        storage.update_payment(
            reference_id=reference_id,
            recipient_signature=recipient_signature,
            status=P2MPaymentStatus.APPROVED,
        )

        return utils.jws_response(
            reference_id,
            result_object=InitChargePaymentResponse(
                recipient_signature=recipient_signature
            ),
        )
    else:
        storage.update_payment(
            reference_id=reference_id, status=P2MPaymentStatus.APPROVED
        )
        return utils.jws_response(reference_id)


def sign_as_receiver(reference_id, sender_address, amount):
    sender_address, _ = utils.account_address_and_subaddress(sender_address)

    sig_msg = txnmetadata.travel_rule(reference_id, sender_address, amount)[1]

    return utils.compliance_private_key().sign(sig_msg).hex()


def handle_init_authorize_command(request: CommandRequestObject):
    reference_id = request.command.reference_id

    return utils.jws_response(reference_id)


def handle_abort_payment_command(request: CommandRequestObject):
    reference_id = request.command.reference_id

    payment_model = storage.get_payment_details(reference_id)

    if not payment_model:
        raise P2MPaymentNotFoundError(f"Could not find payment {reference_id}")

    storage.update_payment(reference_id=reference_id, status=P2MPaymentStatus.REJECTED)

    return utils.jws_response(reference_id)
