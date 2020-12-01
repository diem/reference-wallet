# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import context, secrets
from operator import attrgetter
from typing import Dict, List, Optional

from diem import identifier
from diem_utils.precise_amount import Amount
from diem_utils.types.currencies import DiemCurrency, FiatCurrency
from diem_utils.types.liquidity.currency import Currency
from wallet import storage
from wallet.services import transaction as transaction_service
from wallet.services.fx.fx import get_rate
from wallet.storage import (
    get_account_id_from_subaddr,
    Transaction,
    get_account,
    add_subaddress,
    is_subaddress_exists,
    Account,
    User,
)
from wallet.types import (
    Balance,
    TransactionStatus,
    TransactionDirection,
    TransactionSortOption,
)


def create_account(account_name: str, user_id: Optional[int] = None) -> Account:
    if not account_name:
        raise ValueError("account must have a unique name")

    return storage.create_account(account_name=account_name, user_id=user_id)


def is_in_wallet(receiver_subaddress, receiver_vasp) -> bool:
    return (
        get_account_id_from_subaddr(receiver_subaddress) is not None
        and receiver_vasp == context.get().config.vasp_address
    )


def is_own_address(sender_id, receiver_vasp, receiver_subaddress) -> bool:
    return (
        receiver_vasp == context.get().config.vasp_address
        and get_account_id_from_subaddr(receiver_subaddress) == sender_id
    )


def get_account_transactions(
    account_id: Optional[int] = None,
    account_name: Optional[str] = None,
    currency: Optional[DiemCurrency] = None,
    direction_filter: Optional[TransactionDirection] = None,
    limit: Optional[int] = None,
    sort: Optional[TransactionSortOption] = None,
    up_to_version=None,
) -> List[Transaction]:
    if not account_id:
        account = get_account(account_name=account_name)
        account_id = account.id

    txs = storage.get_account_transactions(
        account_id=account_id, currency=currency, up_to_version=up_to_version
    )

    if direction_filter:
        txs[:] = [
            tx
            for tx in txs
            if transaction_service.get_transaction_direction(account_id, tx)
            == direction_filter
        ]

    fiat_currency = None

    if sort:
        if (
            sort == TransactionSortOption.FIAT_AMOUNT_DESC
            or sort == TransactionSortOption.FIAT_AMOUNT_ASC
        ):
            user = storage.get_user_by_account_id(account_id)
            fiat_currency = FiatCurrency[user.selected_fiat_currency]

        _sort_transactions(
            txs=txs, sort_option=sort, fiat_currency_to_sort_by=fiat_currency
        )

    return txs[:limit]


def _sort_transactions(
    txs: List[Transaction],
    sort_option: TransactionSortOption,
    fiat_currency_to_sort_by: Optional[FiatCurrency] = None,
):
    if sort_option == TransactionSortOption.DATE_ASC:
        txs.sort(key=attrgetter("created_timestamp"))
    elif sort_option == TransactionSortOption.DATE_DESC:
        txs.sort(key=attrgetter("created_timestamp"), reverse=True)
    elif sort_option == TransactionSortOption.DIEM_AMOUNT_ASC:
        txs.sort(key=attrgetter("amount"))
    elif sort_option == TransactionSortOption.DIEM_AMOUNT_DESC:
        txs.sort(key=attrgetter("amount"), reverse=True)
    elif sort_option == TransactionSortOption.FIAT_AMOUNT_ASC:
        _sort_transactions_by_fiat_amount(txs, fiat_currency_to_sort_by)
    elif sort_option == TransactionSortOption.FIAT_AMOUNT_DESC:
        _sort_transactions_by_fiat_amount(txs, fiat_currency_to_sort_by, reverse=True)
    else:
        # Sort option not implemented
        pass


def _sort_transactions_by_fiat_amount(
    txs: List[Transaction], fiat_currency: FiatCurrency, reverse=False
):
    latest_rates = _get_rates()

    def tx_fiat_amount(tx: Transaction):
        rate = latest_rates[f"{tx.currency}_{fiat_currency}"]
        tx_amount = Amount().deserialize(tx.amount)
        fiat_amount = rate * tx_amount
        return fiat_amount.serialize()

    txs.sort(key=tx_fiat_amount, reverse=reverse)


def _get_rates() -> Dict[str, Amount]:
    rates = {}

    for base_currency in DiemCurrency.__members__:
        for fiat_currency in FiatCurrency.__members__:
            try:
                rate = get_rate(
                    base_currency=Currency(base_currency),
                    quote_currency=Currency(fiat_currency),
                )

                rates[f"{base_currency}_{fiat_currency}"] = rate
            except LookupError:
                pass

    return rates


def get_account_balance_by_name(
    account_name: Optional[str] = None, up_to_version=None,
):
    account = get_account(account_name=account_name)

    return get_account_balance(account, up_to_version)


def get_account_balance_by_id(
    account_id: Optional[int] = None, up_to_version=None,
) -> Balance:
    account = get_account(account_id=account_id)

    return get_account_balance(account, up_to_version)


def get_account_balance(account, up_to_version=None):
    account_transactions = get_account_transactions(
        account_id=account.id, up_to_version=up_to_version
    )

    return calc_account_balance(
        account_id=account.id, transactions=account_transactions
    )


def calc_account_balance(account_id: int, transactions: List[Transaction]) -> Balance:
    account_balance = Balance()
    for tx in transactions:
        if tx.destination_id == account_id and tx.status == TransactionStatus.COMPLETED:
            account_balance.total[DiemCurrency[tx.currency]] += tx.amount
        if tx.source_id == account_id:
            if tx.status == TransactionStatus.PENDING:
                account_balance.frozen[DiemCurrency[tx.currency]] += tx.amount
            if tx.status != TransactionStatus.CANCELED:
                account_balance.total[DiemCurrency[tx.currency]] -= tx.amount

    return account_balance


def generate_new_subaddress(account_id: int) -> str:
    sub_address = generate_sub_address()
    add_subaddress(account_id=account_id, subaddr=sub_address)

    return sub_address


def generate_sub_address():
    sub_address = None

    while not sub_address:
        sub_address = secrets.token_hex(identifier.DIEM_SUBADDRESS_SIZE)
        # generated subaddress is unique
        if is_subaddress_exists(sub_address):
            sub_address = None

    return sub_address


def get_deposit_address(
    account_id: Optional[int] = None, account_name: Optional[str] = None
):
    account = get_account(account_id=account_id, account_name=account_name)
    subaddress = generate_new_subaddress(account.id)

    return identifier.encode_account(
        context.get().config.vasp_account_address(),
        subaddress,
        context.get().config.diem_address_hrp(),
    )


def is_user_allowed_for_account(user: User, account_name: str) -> bool:
    if user.is_admin:
        return True

    if user.account is None:
        return False

    return user.account.name == account_name
