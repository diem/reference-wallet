# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from .command_types import (
    OffChainErrorType,
    ErrorCode,
    CommandResponseObject,
    OffChainErrorObject,
    CommandRequestObject,
    CommandResponseStatus,
    ResponseType,
)
from .payment_command_types import (
    AbortCode,
    NationalIdObject,
    AddressObject,
    Status,
    StatusObject,
    PaymentObject,
    PaymentActorObject,
    PaymentActionObject,
    KycDataObject,
    KycDataObjectType,
    CommandType,
    PaymentCommandObject,
)
from .fund_pull_pre_approval_types import (
    FundPullPreApprovalObject,
    FundPullPreApprovalStatus,
    FundPullPreApprovalScopeObject,
    ScopedCumulativeAmountObject,
    TimeUnit,
    CurrencyObject,
    FundPullPreApprovalType,
    FundPullPreApprovalCommandObject,
)
from .payment_types import (
    GetInfoCommandObject,
    GetInfoCommandResponse,
    PaymentInfoObject,
    PaymentReceiverObject,
    BusinessDataObject,
    InitChargeCommand,
    PaymentSenderObject,
    PayerDataObject,
    InitAuthorizeCommand,
    InitChargeCommandResponse,
)

import dataclasses, json, re, typing, uuid


class FieldError(ValueError):
    def __init__(self, code: str, field: str, msg: str) -> None:
        super().__init__(msg)
        self.code: str = code
        self.field: typing.Optional[str] = field if field else None


class InvalidOverwriteError(FieldError):
    def __init__(
        self,
        field: str,
        prior_value: typing.Any,
        new_value: typing.Any,
        field_type: str,  # pyre-ignore
    ) -> None:
        msg = f"{field_type} field '{field}': {prior_value} => {new_value}"
        super().__init__(ErrorCode.invalid_overwrite, field, msg)


T = typing.TypeVar("T")

_OBJECT_TYPES: typing.Dict[str, typing.Any] = {
    "CommandResponseObject": CommandResponseObject,
    "CommandRequestObject": CommandRequestObject,
    CommandType.PaymentCommand: PaymentCommandObject,
    CommandType.FundPullPreApprovalCommand: FundPullPreApprovalCommandObject,
    CommandType.GetInfoCommand: GetInfoCommandObject,
    ResponseType.GetInfoCommandResponse: GetInfoCommandResponse,
    ResponseType.InitChargeCommandResponse: InitChargeCommandResponse,
}

_OBJECT_TYPE_FIELD_NAME = "_ObjectType"


def to_json(obj: T, indent: typing.Optional[int] = None) -> str:
    if dataclasses.is_dataclass(obj):
        raw = dataclasses.asdict(obj)
    elif isinstance(obj, list):
        raw = list(map(dataclasses.asdict, obj))
    else:
        raw = obj
    return json.dumps(_delete_none(raw), indent=indent)


def from_json(data: str, klass: typing.Optional[typing.Type[T]] = None) -> T:
    return from_dict(json.loads(data), klass)


def from_dict(
    obj: typing.Any, klass: typing.Optional[typing.Type[T]], field_path: str = ""
) -> T:  # pyre-ignore
    if klass is None or _is_union(klass):
        if not isinstance(obj, dict):
            code = (
                ErrorCode.invalid_field_value
                if field_path
                else ErrorCode.invalid_object
            )
            raise FieldError(
                code,
                field_path,
                f"expect json object, but got {type(obj).__name__}: {obj}",
            )
        klass = _find_object_type(obj, field_path)
    return _from_dict(obj, klass, field_path)


def _from_dict(
    obj: typing.Any, klass: typing.Type[typing.Any], field_path: str
) -> typing.Any:  # pyre-ignore
    if not isinstance(obj, dict) or not dataclasses.is_dataclass(klass):
        item_type = None
        if (
            hasattr(klass, "__origin__")
            and klass.__origin__ == list
            and hasattr(klass, "__args__")
        ):
            item_type = klass.__args__[0]
            klass = list
        if not isinstance(obj, klass):
            code = (
                ErrorCode.invalid_field_value
                if field_path
                else ErrorCode.invalid_object
            )
            raise FieldError(
                code,
                field_path,
                f"expect type {klass.__name__}, but got {type(obj).__name__}",
            )
        if klass == list and item_type:
            return [from_dict(item, item_type, field_path) for item in obj]
        return obj

    unknown_fields = list(obj.keys())
    for field in dataclasses.fields(klass):
        if field.name in unknown_fields:
            unknown_fields.remove(field.name)
        obj[field.name] = _field_value_from_dict(field, obj, field_path)

    if len(unknown_fields) > 0:
        unknown_fields.sort()
        full_name = _join_field_path(field_path, unknown_fields[0])
        field_names = ", ".join(unknown_fields)
        raise FieldError(
            ErrorCode.unknown_field, full_name, f"{field_path}: {field_names}"
        )
    return klass(**obj)


def _field_value_from_dict(
    field: dataclasses.Field, obj: typing.Any, field_path: str
) -> typing.Any:  # pyre-ignore
    full_name = _join_field_path(field_path, field.name)
    field_type = field.type
    args = field.type.__args__ if hasattr(field.type, "__args__") else []
    is_optional = len(args) == 2 and isinstance(None, args[1])  # pyre-ignore
    if is_optional:
        field_type = args[0]
    val = obj.get(field.name)
    if val is None:
        if is_optional:
            return None
        raise FieldError(
            ErrorCode.missing_field, full_name, f"missing field: {full_name}"
        )

    valid_values = field.metadata.get("valid-values")
    if valid_values:
        if isinstance(valid_values, list) and val not in valid_values:
            raise FieldError(
                ErrorCode.invalid_field_value,
                full_name,
                f"expect one of {valid_values}, but got: {val}",
            )
        if isinstance(valid_values, re.Pattern) and not valid_values.match(val):
            raise FieldError(
                ErrorCode.invalid_field_value,
                full_name,
                f"{val} does not match pattern {valid_values.pattern}",
            )
    return from_dict(val, field_type, full_name)


def _join_field_path(path: str, field: str) -> str:
    return f"{path}.{field}" if path else field


def new_payment_object(
    sender_account_id: str,
    sender_kyc_data: KycDataObject,
    receiver_account_id: str,
    amount: int,
    currency: str,
    original_payment_reference_id: typing.Optional[str] = None,
    description: typing.Optional[str] = None,
) -> PaymentObject:
    """Initialize a payment request command

    returns generated reference_id and created `CommandRequestObject`
    """

    return PaymentObject(
        reference_id=str(uuid.uuid4()),
        sender=PaymentActorObject(
            address=sender_account_id,
            kyc_data=sender_kyc_data,
            status=StatusObject(status=Status.needs_kyc_data),
        ),
        receiver=PaymentActorObject(
            address=receiver_account_id,
            status=StatusObject(status=Status.none),
        ),
        action=PaymentActionObject(amount=amount, currency=currency),
        description=description,
        original_payment_reference_id=original_payment_reference_id,
    )


def replace_payment_actor(
    actor: PaymentActorObject,
    status: typing.Optional[str] = None,
    kyc_data: typing.Optional[KycDataObject] = None,
    additional_kyc_data: typing.Optional[str] = None,
    abort_code: typing.Optional[str] = None,
    abort_message: typing.Optional[str] = None,
    metadata: typing.Optional[typing.List[str]] = None,
) -> PaymentActorObject:
    changes = {}
    if kyc_data:
        changes["kyc_data"] = kyc_data
    if additional_kyc_data:
        changes["additional_kyc_data"] = additional_kyc_data
    if status or abort_code or abort_message:
        changes["status"] = replace_payment_status(
            actor.status,
            status=status,
            abort_code=abort_code,
            abort_message=abort_message,
        )
    if metadata:
        if not isinstance(metadata, list):
            raise ValueError("metadata should be a list of string")
        changes["metadata"] = actor.metadata + metadata if actor.metadata else metadata
    return dataclasses.replace(actor, **changes)


def replace_payment_status(
    status_obj: StatusObject,
    status: typing.Optional[str] = None,
    abort_code: typing.Optional[str] = None,
    abort_message: typing.Optional[str] = None,
) -> StatusObject:
    changes = {}
    if status:
        changes["status"] = status
    if abort_code:
        changes["abort_code"] = abort_code
    if abort_message:
        changes["abort_message"] = abort_message
    return dataclasses.replace(status_obj, **changes)


def new_payment_request(
    payment: PaymentObject,
    cid: typing.Optional[str] = None,
) -> CommandRequestObject:
    return CommandRequestObject(
        cid=cid or str(uuid.uuid4()),
        command_type=CommandType.PaymentCommand,
        command=PaymentCommandObject(
            _ObjectType=CommandType.PaymentCommand,
            payment=payment,
        ),
    )


def new_funds_pull_pre_approval_request(
    funds_pull_pre_approval: FundPullPreApprovalObject,
    cid: typing.Optional[str] = None,
) -> CommandRequestObject:
    return CommandRequestObject(
        cid=cid or str(uuid.uuid4()),
        command_type=CommandType.FundPullPreApprovalCommand,
        command=FundPullPreApprovalCommandObject(
            _ObjectType=CommandType.FundPullPreApprovalCommand,
            fund_pull_pre_approval=funds_pull_pre_approval,
        ),
    )


def new_get_info_request(
    reference_id: str,
    cid: typing.Optional[str] = None,
) -> CommandRequestObject:
    return CommandRequestObject(
        cid=cid or reference_id or str(uuid.uuid4()),
        command_type=CommandType.GetInfoCommand,
        command=GetInfoCommandObject(
            _ObjectType=CommandType.GetInfoCommand,
            reference_id=reference_id,
        ),
    )


def new_payment_info_object(
    reference_id: str,
    receiver_address: str,
    name: str,
    legal_name: str,
    city: str,
    country: str,
    line1: str,
    line2: str,
    postal_code: str,
    state: str,
    amount: int,
    currency: str,
    action: str,
    timestamp: int,
    valid_until: typing.Optional[int] = None,
    description: typing.Optional[str] = None,
):
    return PaymentInfoObject(
        receiver=PaymentReceiverObject(
            address=receiver_address,
            business_data=BusinessDataObject(
                name=name,
                legal_name=legal_name,
                address=new_address_object(
                    city=city,
                    country=country,
                    line1=line1,
                    line2=line2,
                    postal_code=postal_code,
                    state=state,
                ),
            ),
        ),
        action=PaymentActionObject(
            amount=amount,
            currency=currency,
            action=action,
            timestamp=timestamp,
            valid_until=valid_until,
        ),
        reference_id=reference_id,
        description=description,
    )


def new_init_auth_command(
    reference_id,
    vasp_address,
    sender_name,
    sender_sure_name,
    sender_city,
    sender_country,
    sender_line1,
    sender_line2,
    sender_postal_code,
    sender_state,
    sender_national_id_value,
    sender_national_id_type,
):
    return new_init_command(
        CommandType.InitAuthorizeCommand,
        reference_id,
        sender_city,
        sender_country,
        sender_line1,
        sender_line2,
        sender_name,
        sender_national_id_type,
        sender_national_id_value,
        sender_postal_code,
        sender_state,
        sender_sure_name,
        vasp_address,
    )


def new_init_charge_command(
    reference_id,
    vasp_address,
    sender_name,
    sender_sure_name,
    sender_city,
    sender_country,
    sender_line1,
    sender_line2,
    sender_postal_code,
    sender_state,
    sender_national_id_value,
    sender_national_id_type,
):
    return new_init_command(
        CommandType.InitChargeCommand,
        reference_id,
        sender_city,
        sender_country,
        sender_line1,
        sender_line2,
        sender_name,
        sender_national_id_type,
        sender_national_id_value,
        sender_postal_code,
        sender_state,
        sender_sure_name,
        vasp_address,
    )


def new_init_command(
    command_type,
    reference_id,
    sender_city,
    sender_country,
    sender_line1,
    sender_line2,
    sender_name,
    sender_national_id_type,
    sender_national_id_value,
    sender_postal_code,
    sender_state,
    sender_sure_name,
    vasp_address,
):
    return CommandRequestObject(
        cid=reference_id or str(uuid.uuid4()),
        command_type=command_type,
        command=InitChargeCommand(
            reference_id=reference_id,
            sender=new_payment_sender_object(
                sender_city,
                sender_country,
                sender_line1,
                sender_line2,
                sender_name,
                sender_sure_name,
                sender_national_id_type,
                sender_national_id_value,
                sender_postal_code,
                sender_state,
                vasp_address,
            ),
        ),
    )


def new_payment_sender_object(
    city,
    country,
    line1,
    line2,
    my_name,
    my_sure_name,
    national_id_type,
    national_id_value,
    postal_code,
    state,
    vasp_address,
):
    return PaymentSenderObject(
        account_address=vasp_address,
        payer_data=new_payer_data_object(
            city,
            country,
            line1,
            line2,
            my_name,
            my_sure_name,
            national_id_type,
            national_id_value,
            postal_code,
            state,
        ),
    )


def new_payer_data_object(
    city,
    country,
    line1,
    line2,
    my_name,
    my_sure_name,
    national_id_type,
    national_id_value,
    postal_code,
    state,
):
    return PayerDataObject(
        given_name=my_name,
        surname=my_sure_name,
        address=new_address_object(
            city=city,
            country=country,
            line1=line1,
            line2=line2,
            postal_code=postal_code,
            state=state,
        ),
        national_id=new_national_id_object(
            country, national_id_type, national_id_value
        ),
    )


def new_national_id_object(country, national_id_type, national_id_value):
    return NationalIdObject(
        id_value=national_id_value,
        country=country,
        type=national_id_type,
    )


def new_address_object(city, country, line1, line2, postal_code, state):
    return AddressObject(
        city=city,
        country=country,
        line1=line1,
        line2=line2,
        postal_code=postal_code,
        state=state,
    )


def reply_request(
    cid: typing.Optional[str],
    result_object: typing.Optional[typing.Union[GetInfoCommandResponse]] = None,
    err: typing.Optional[OffChainErrorObject] = None,
) -> CommandResponseObject:
    return CommandResponseObject(
        status=CommandResponseStatus.failure if err else CommandResponseStatus.success,
        error=err,
        cid=cid,
        result=result_object,
    )


def individual_kyc_data(**kwargs) -> KycDataObject:  # pyre-ignore
    return KycDataObject(
        type=KycDataObjectType.individual,
        **kwargs,
    )


def entity_kyc_data(**kwargs) -> KycDataObject:  # pyre-ignore
    return KycDataObject(
        type=KycDataObjectType.entity,
        **kwargs,
    )


def validate_write_once_fields(
    path: str, new: typing.Any, prior: typing.Any
) -> None:  # pyre-ignore
    if new is None or prior is None:
        return

    new_type = type(new)
    if type(prior) != new_type:
        raise TypeError(
            f"field {path} type is different, expect {type(prior)}, but got {new_type}"
        )

    if not dataclasses.is_dataclass(new_type):
        return

    for field in dataclasses.fields(new_type):
        prior_value = getattr(prior, field.name)
        new_value = getattr(new, field.name)
        field_path = path + "." + field.name
        if field.metadata.get("immutable") and prior_value != new_value:
            raise InvalidOverwriteError(field_path, prior_value, new_value, "immutable")
        if (
            field.metadata.get("write_once")
            and prior_value is not None
            and prior_value != new_value
        ):
            raise InvalidOverwriteError(
                field_path, prior_value, new_value, "write once"
            )
        validate_write_once_fields(field_path, new_value, prior_value)


def _delete_none(obj: typing.Any) -> typing.Any:  # pyre-ignore
    if isinstance(obj, dict):
        for key, val in list(obj.items()):
            if val is None:
                del obj[key]
            else:
                obj[key] = _delete_none(val)
    elif isinstance(obj, list):
        for val in obj:
            _delete_none(val)
    return obj


def _find_object_type(
    obj: typing.Dict[str, typing.Any], field_path: str
) -> typing.Type[typing.Any]:  # pyre-ignore
    obj_type = obj.get(_OBJECT_TYPE_FIELD_NAME)
    full_name = _join_field_path(field_path, _OBJECT_TYPE_FIELD_NAME)
    if not obj_type:
        raise FieldError(
            ErrorCode.missing_field, full_name, f"missing field: {full_name}"
        )
    t = _OBJECT_TYPES.get(obj_type)
    if t is None:
        raise FieldError(
            ErrorCode.invalid_field_value,
            full_name,
            f"could not find object type: {obj_type}, valid types: {list(_OBJECT_TYPES.keys())}",
        )
    return t


def _is_union(klass: typing.Any) -> bool:  # pyre-ignore
    return hasattr(klass, "__origin__") and klass.__origin__ == typing.Union
