import dataclasses
import typing
import logging

from diem_utils.types.currencies import DiemCurrency
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
from wallet.storage.models import PaymentInfo as PaymentInfoModel
from wallet.storage.payment import save_payment_info
from wallet.services.offchain import utils
from wallet import storage

logger = logging.getLogger(__name__)


def handle_get_info_command(request: CommandRequestObject):
    # The get_info command arrive only when LRW playing the Merchant\Receiver role in the communication,
    # and therefore we can assume that the payment info have been generated in advance
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
        timestamp=payment_info_model.expiration,
        description=payment_info_model.description,
    )

    return utils.jws_response(request.cid, result_object=payment_info_object)


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


def get_payment_info(account_id, reference_id: str, vasp_address):
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
        raise P2MGeneralError(e)

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

    return None
