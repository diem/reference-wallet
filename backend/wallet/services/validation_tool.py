import uuid

import context
from diem import identifier
from diem.offchain import (
    CommandType,
    TimeUnit,
    ScopedCumulativeAmountObject,
    CurrencyObject,
    FundPullPreApprovalScopeObject,
    FundPullPreApprovalType,
    FundPullPreApprovalObject,
    FundPullPreApprovalCommandObject,
    CommandRequestObject,
)
from diem_utils.types.currencies import DiemCurrency
from wallet.services.account import generate_new_subaddress


def create_funds_pull_pre_approval_request(
    user_account_id: int,
    address: str,
    expiration_time: int,
    description: str,
    max_cumulative_amount: int,
    currency: DiemCurrency,
    cumulative_amount_unit: str,  # should be TimeUnit
    cumulative_amount_unit_value: int,
):
    max_cumulative_amount_object = ScopedCumulativeAmountObject(
        unit=cumulative_amount_unit,
        value=cumulative_amount_unit_value,
        max_amount=CurrencyObject(amount=max_cumulative_amount, currency=currency),
    )

    scope = FundPullPreApprovalScopeObject(
        type=FundPullPreApprovalType.consent,
        expiration_timestamp=expiration_time,
        max_cumulative_amount=max_cumulative_amount_object,
    )

    biller_address = get_biller_address(user_account_id)

    funds_pull_pre_approval_id = str(uuid.UUID())

    funds_pull_pre_approval = FundPullPreApprovalObject(
        address=address,
        biller_address=biller_address,
        funds_pull_pre_approval_id=funds_pull_pre_approval_id,
        scope=scope,
        description=description,
    )

    command = FundPullPreApprovalCommandObject(
        _ObjectType=CommandType.FundPullPreApprovalCommand,
        fund_pull_pre_approval=funds_pull_pre_approval,
    )

    cid = str(uuid.UUID())

    command_object = CommandRequestObject(
        cid=cid,
        command_type=CommandType.FundPullPreApprovalCommand,
        command=command,
    )

    # TODO send to offchain client

    return funds_pull_pre_approval_id


def get_biller_address(user_account_id):
    vasp_address = context.get().config.vasp_address
    sub_address = generate_new_subaddress(user_account_id)
    hrp = context.get().config.diem_address_hrp()

    return identifier.encode_account(vasp_address, sub_address, hrp)
