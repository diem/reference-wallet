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
) -> (str, str):
    return commit_funds_pull_pre_approval(account_id, description, payer_address, scope)


def create_preapproval_for_unknown_payer(
    account_id: int,
    scope: offchain.FundPullPreApprovalScopeObject,
    description: str = None,
) -> (str, str):
    return commit_funds_pull_pre_approval(account_id, description, None, scope, True)


def commit_funds_pull_pre_approval(
    account_id, description, payer_address, scope, offchain_sent=False
) -> (str, str):
    biller_address = get_biller_address(account_id)

    funds_pull_pre_approval_id = generate_funds_pull_pre_approval_id(biller_address)

    max_cumulative_amount = get_max_cumulative_amount_from_scope(scope)
    max_transaction_amount = get_max_transaction_amount_from_scope(scope)

    fppa_storage.commit_command(
        fppa_storage.models.FundsPullPreApprovalCommand(
            account_id=account_id,
            address=payer_address,
            biller_address=biller_address,
            funds_pull_pre_approval_id=funds_pull_pre_approval_id,
            funds_pull_pre_approval_type=scope.type,
            expiration_timestamp=scope.expiration_timestamp,
            description=description,
            status=offchain.FundPullPreApprovalStatus.pending,
            role=Role.PAYEE,
            offchain_sent=offchain_sent,
            **max_cumulative_amount,
            **max_transaction_amount,
        )
    )

    return funds_pull_pre_approval_id, biller_address


def get_max_transaction_amount_from_scope(scope):
    max_transaction_amount = {}
    if scope.max_transaction_amount is not None:
        max_transaction_amount = dict(
            max_transaction_amount=scope.max_transaction_amount.amount,
            max_transaction_amount_currency=scope.max_transaction_amount.currency,
        )

    return max_transaction_amount


def get_max_cumulative_amount_from_scope(scope):
    max_cumulative_amount = {}
    if scope.max_cumulative_amount is not None:
        max_cumulative_amount = dict(
            max_cumulative_unit=scope.max_cumulative_amount.unit,
            max_cumulative_unit_value=scope.max_cumulative_amount.value,
            max_cumulative_amount=scope.max_cumulative_amount.max_amount.amount,
            max_cumulative_amount_currency=scope.max_cumulative_amount.max_amount.currency,
        )

    return max_cumulative_amount


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
