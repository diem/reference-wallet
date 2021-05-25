import typing

from .command_types import CommandType, ResponseType
from dataclasses import dataclass, field as datafield
from .payment_command_types import AddressObject, PaymentActionObject, NationalIdObject


@dataclass(frozen=True)
class GetInfoCommandObject:
    reference_id: str
    _ObjectType: str = datafield(
        default=CommandType.GetInfoCommand,
        metadata={"valid-values": [CommandType.GetInfoCommand]},
    )


@dataclass(frozen=True)
class BusinessDataObject:
    name: str
    legal_name: str
    address: AddressObject


@dataclass(frozen=True)
class PaymentReceiverObject:
    address: str
    business_data: BusinessDataObject


@dataclass(frozen=True)
class PaymentInfoObject:
    receiver: PaymentReceiverObject
    action: PaymentActionObject
    reference_id: str
    description: str


@dataclass(frozen=True)
class GetInfoCommandResponse:
    payment_info: PaymentInfoObject
    _ObjectType: str = datafield(default=ResponseType.GetInfoCommandResponse)


@dataclass(frozen=True)
class InitChargePaymentResponse:
    recipient_signature: typing.Optional[str] = None
    _ObjectType: str = datafield(default=ResponseType.InitChargePaymentResponse)


@dataclass(frozen=True)
class PayerDataObject:
    given_name: str
    surname: str
    address: AddressObject
    national_id: NationalIdObject


@dataclass(frozen=True)
class PaymentSenderObject:
    account_address: str
    payer_data: PayerDataObject


@dataclass(frozen=True)
class InitChargePayment:
    sender: PaymentSenderObject
    reference_id: str
    _ObjectType: str = datafield(default=CommandType.InitChargePayment)


@dataclass(frozen=True)
class InitAuthorizeCommand:
    sender: PaymentSenderObject
    reference_id: str
    _ObjectType: str = datafield(default=CommandType.InitAuthorizeCommand)
