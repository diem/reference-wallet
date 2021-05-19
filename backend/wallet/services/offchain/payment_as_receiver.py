import typing
from datetime import datetime

from diem import txnmetadata
from offchain import CommandRequestObject, GetInfoCommandObject
from offchain.types import (
    new_payment_info_object,
    GetInfoCommandResponse,
    InitChargeCommand,
    InitChargeCommandResponse,
    InitAuthorizeCommand,
)
from wallet import storage
from wallet.services.offchain import utils


def handle_get_info_command(request: CommandRequestObject):
    # The get_info command arrive only when LRW playing the Merchant\Receiver role in the communication,
    # and therefore we can assume that the payment info already been saved in DB
    # and the missing data we can mock
    get_info_command_object = typing.cast(GetInfoCommandObject, request.command)

    reference_id = get_info_command_object.reference_id

    payment_model = storage.get_payment_details(reference_id)

    payment_info_object = new_payment_info_object(
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
    init_charge_command_object = typing.cast(InitChargeCommand, request.command)

    reference_id = init_charge_command_object.reference_id

    payment = storage.get_payment_details(reference_id)

    payment_amount = payment.amount

    if payment_amount > 1_000_000_000:
        recipient_signature = sign_as_receiver(
            reference_id=reference_id,
            sender_address=init_charge_command_object.sender.account_address,
            amount=payment_amount,
        )

        return utils.jws_response(
            reference_id,
            result_object=InitChargeCommandResponse(
                recipient_signature=recipient_signature
            ),
        )
    else:
        return utils.jws_response(reference_id)


def sign_as_receiver(reference_id, sender_address, amount):
    sender_address, _ = utils.account_address_and_subaddress(sender_address)

    sig_msg = txnmetadata.travel_rule(reference_id, sender_address, amount)[1]

    return utils.compliance_private_key().sign(sig_msg).hex()


def handle_init_authorize_command(request: CommandRequestObject):
    init_auth_command_object = typing.cast(InitAuthorizeCommand, request.command)

    reference_id = init_auth_command_object.reference_id

    return utils.jws_response(reference_id)
