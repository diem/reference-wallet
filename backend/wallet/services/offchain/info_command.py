import dataclasses
import logging
import typing
from datetime import datetime

from offchain import (
    GetInfoCommandObject,
    CommandRequestObject,
    jws,
)
from offchain.types import (
    new_payment_info_object,
    new_get_info_request,
    GetInfoCommandResponse,
)
from wallet import storage
from wallet.services.offchain import utils
from wallet.storage.models import PaymentInfo as PaymentInfoModel
from wallet.storage.payment_info import save_payment_info

logger = logging.getLogger(__name__)


def handle_get_info_command(request: CommandRequestObject):
    # The get_info command arrive only when LRW playing the Merchant\Receiver role in the communication,
    # and therefore we can assume that the payment info already been saved in DB
    info_command_object = typing.cast(GetInfoCommandObject, request.command)

    reference_id = info_command_object.reference_id

    payment_info_model = storage.get_payment_info(reference_id)

    payment_info_object = new_payment_info_object(
        reference_id=reference_id,
        receiver_address=payment_info_model.vasp_address,
        name=payment_info_model.merchant_name,
        legal_name=payment_info_model.merchant_legal_name,
        city=payment_info_model.city,
        country=payment_info_model.country,
        line1=payment_info_model.line1,
        line2=payment_info_model.line2,
        postal_code=payment_info_model.postal_code,
        state=payment_info_model.state,
        amount=payment_info_model.amount,
        currency=payment_info_model.currency,
        action=payment_info_model.action,
        timestamp=int(datetime.timestamp(payment_info_model.created_at)),
        valid_until=int(datetime.timestamp(payment_info_model.expiration))
        if payment_info_model.action == "auth"
        else None,
        description=payment_info_model.description,
    )

    return utils.jws_response(
        request.cid,
        result_object=GetInfoCommandResponse(payment_info=payment_info_object),
    )


@dataclasses.dataclass(frozen=True)
class PaymentInfo:
    vasp_address: str
    reference_id: str
    merchant_name: str
    action: str
    currency: str
    amount: int
    expiration: int


class P2MGeneralError(Exception):
    pass


def get_payment_info(account_id, reference_id: str, vasp_address: str):
    payment_info_model = storage.get_payment_info(reference_id)

    if payment_info_model is None:
        my_address = utils.generate_my_address(account_id)

        try:
            command_response_object = utils.offchain_client().send_request(
                request_sender_address=my_address,
                counterparty_account_id=vasp_address,
                request_bytes=jws.serialize(
                    new_get_info_request(reference_id=reference_id, cid=reference_id),
                    utils.compliance_private_key().sign,
                ),
            )
        except Exception as e:
            error = P2MGeneralError(e)
            logger.error(error)
            raise error

        if (
            command_response_object.result
            and type(command_response_object.result) is GetInfoCommandResponse
        ):
            payment_info = command_response_object.result.payment_info
            action_object = payment_info.action

            payment_info_model = save_payment_info(
                PaymentInfoModel(
                    vasp_address=vasp_address,
                    reference_id=reference_id,
                    merchant_name=payment_info.receiver.business_data.name,
                    action=action_object.action,
                    currency=action_object.currency,
                    amount=action_object.amount,
                    expiration=datetime.fromtimestamp(action_object.valid_until)
                    if action_object.valid_until
                    else None,
                )
            )

    return PaymentInfo(
        vasp_address=payment_info_model.vasp_address,
        reference_id=payment_info_model.reference_id,
        merchant_name=payment_info_model.merchant_name,
        action=payment_info_model.action,
        currency=payment_info_model.currency,
        amount=payment_info_model.amount,
        expiration=int(datetime.timestamp(payment_info_model.expiration))
        if payment_info_model.expiration
        else None,
    )
