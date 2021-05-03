import dataclasses
import typing
import logging

from offchain import (
    GetInfoCommandObject,
    CommandRequestObject,
    jws,
)
from offchain.types import (
    new_payment_info_object,
    new_info_request,
    GetInfoCommandResponse,
)
from wallet import storage
from wallet.storage.models import PaymentInfo as PaymentInfoModel
from wallet.storage.payment import save_payment_info
from wallet.services.offchain import utils

logger = logging.getLogger(__name__)


def handle_get_info_command(request: CommandRequestObject):
    # This command arrive only when LRW playing the Merchant\Receiver role in the communication,
    # and therefore we can assume that a PaymentCommand is already saved in DB
    info_command_object = typing.cast(GetInfoCommandObject, request.command)

    # save_payment_command_as_receiver(payment_command)

    reference_id = info_command_object.reference_id
    model = storage.get_payment_command(reference_id)
    payment_info = new_payment_info_object(
        reference_id=reference_id,
        receiver_address=model.my_actor_address,
        name="Bond & Gurki Pet Store",
        legal_name="Bond & Gurki Pet Store",
        city="Dogcity",
        country="Dogland",
        line1="1234 Puppy Street",
        line2="dogpalace 3",
        postal_code="123456",
        state="Dogstate",
        amount=model.amount,
        currency=model.currency,
        action=model.action,
        timestamp=model.created_at,
        valid_until=model.expiration,
        description=model.description,
    )
    # return jws(cid=reference_id, result_object=payment_info)
    return None


@dataclasses.dataclass(frozen=True)
class PaymentInfo:
    vasp_address: str
    reference_id: str
    merchant_name: str
    action: str
    currency: str
    amount: int
    expiration: int


def get_payment_info(account_id, reference_id: str, vasp_address):
    my_address = utils.generate_my_address(account_id)

    command_response_object = utils.offchain_client().send_request(
        request_sender_address=my_address,
        counterparty_account_id=vasp_address,
        request_bytes=jws.serialize(
            new_info_request(reference_id=reference_id, cid=reference_id),
            utils.compliance_private_key().sign,
        ),
    )

    if command_response_object.status == "success":
        if (
            command_response_object.result
            and type(command_response_object.result) is GetInfoCommandResponse
        ):
            payment_info = command_response_object.result.payment_info
            action_object = payment_info.action

            save_payment_info(
                PaymentInfoModel(
                    vasp_address=vasp_address,
                    reference_id=reference_id,
                    merchant_name=payment_info.receiver.business_data.name,
                    action=action_object.action,
                    currency=action_object.currency,
                    amount=action_object.amount,
                    expiration=action_object.valid_until,
                )
            )

            return PaymentInfo(
                vasp_address=vasp_address,
                reference_id=reference_id,
                merchant_name=payment_info.receiver.business_data.name,
                action=action_object.action,
                currency=action_object.currency,
                amount=action_object.amount,
                expiration=action_object.valid_until,
            )
    else:
        # todo send request failed
        ...

    return None
