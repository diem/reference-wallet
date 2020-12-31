import uuid

import context
from diem import identifier
from diem.offchain import (
    CommandType,
)
from diem_utils.types.currencies import DiemCurrency
from wallet.services.account import generate_new_subaddress
from wallet.services.stubs import (
    CurrencyObject,
    ScopeObject,
    FundPullPreApprovalObject,
    FundPullPreApprovalCommandObject,
    CommandRequestObject,
    ScopeType,
    ScopedCumulativeAmountObject,
    ScopeUnitType,
)


def send_consent_request(
    user_account_id,
    address,
    expiration_time,
    description,
    max_cumulative_amount,
    currency=DiemCurrency.XUS,
):
    max_cumulative_amount_object = ScopedCumulativeAmountObject(
        unit=ScopeUnitType.WEEK,
        value=1,
        max_amount=CurrencyObject(amount=max_cumulative_amount, currency=currency),
    )

    scope = ScopeObject(
        type=ScopeType.CONSENT,
        expiration_time=expiration_time,
        max_cumulative_amount=max_cumulative_amount_object,
    )

    biller_address = get_biller_address(user_account_id)

    funds_pre_approval_id = str(uuid.UUID())

    fund_pull_pre_approval = FundPullPreApprovalObject(
        address=address,
        biller_address=biller_address,
        funds_pre_approval_id=funds_pre_approval_id,
        scope=scope,
        description=description,
    )

    command = FundPullPreApprovalCommandObject(
        _ObjectType=CommandType.FundPullPreApprovalCommand,
        fund_pull_pre_approval=fund_pull_pre_approval,
    )

    cid = str(uuid.UUID())

    command_object = CommandRequestObject(
        cid=cid,
        command_type=CommandType.FundPullPreApprovalCommand,
        command=command,
    )

    # TODO send to offchain client

    return funds_pre_approval_id


def get_biller_address(user_account_id):
    vasp_address = context.get().config.vasp_address
    sub_address = generate_new_subaddress(user_account_id)
    hrp = context.get().config.diem_address_hrp()
    biller_address = identifier.encode_account(vasp_address, sub_address, hrp)
    return biller_address
