import uuid

import context
from diem import identifier, offchain
from wallet.services.account import generate_new_subaddress
from wallet.storage import funds_pull_pre_approval_command as fppa_storage

from .fund_pull_pre_approval import Role


def request_funds_pull_pre_approval_from_another(
    account_id: int,
    payer_address: str,
    scope: offchain.FundPullPreApprovalScopeObject,
    description: str = None,
) -> str:
    biller_address = get_biller_address(account_id)
    funds_pull_pre_approval_id = generate_funds_pull_pre_approval_id(biller_address)

    fppa_storage.commit_command(
        fppa_storage.models.FundsPullPreApprovalCommand(
            account_id=account_id,
            address=payer_address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type=scope.type,
            expiration_timestamp=scope.expiration_timestamp,
            max_cumulative_unit=scope.max_cumulative_amount.unit,
            max_cumulative_unit_value=scope.max_cumulative_amount.value,
            max_cumulative_amount=scope.max_cumulative_amount.max_amount.amount,
            max_cumulative_amount_currency=scope.max_cumulative_amount.max_amount.currency,
            max_transaction_amount=scope.max_transaction_amount.amount,
            max_transaction_amount_currency=scope.max_transaction_amount.currency,
            description=description,
            status=offchain.FundPullPreApprovalStatus.valid,
            role=Role.PAYER,
        )
    )

    # TODO send to offchain client

    return funds_pull_pre_approval_id


def get_biller_address(user_account_id):
    vasp_address = context.get().config.vasp_address
    sub_address = generate_new_subaddress(user_account_id)
    hrp = context.get().config.diem_address_hrp()

    return identifier.encode_account(vasp_address, sub_address, hrp)


def generate_funds_pull_pre_approval_id(biller_address):
    """
    Generates a new ID in the format mandated by DIP-8.
    """
    random_unique_hex = uuid.uuid4().hex
    return f"{biller_address}_{random_unique_hex}"
