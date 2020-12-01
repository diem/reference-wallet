# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from typing import Optional
from uuid import UUID

import context
from diem import utils
from diem.identifier import decode_account
from diem_utils.sdks.liquidity import LpClient
from diem_utils.types.currencies import DiemCurrency
from diem_utils.types.liquidity.currency import Currency, CurrencyPairs, CurrencyPair
from diem_utils.types.liquidity.quote import QuoteData
from diem_utils.types.liquidity.trade import TradeStatus, TradeData, TradeId
from wallet.logging import log_execution
from wallet.services import INVENTORY_ACCOUNT_NAME
from wallet.services.account import get_deposit_address, create_account
from wallet.services.transaction import send_transaction, get_transaction
from wallet.storage import Order, update_order, get_account
from wallet.types import (
    Direction,
    CoverStatus,
    OrderId,
    TransactionStatus,
)

logger = logging.getLogger(__name__)

INVENTORY_COVER_CURRENCY = Currency.USD
INVENTORY_AMOUNT = 950_000_000


def wait_for_trade_to_complete(trade_id):
    retries = 10
    polling_interval_s = 2
    for _ in range(retries):
        trade_info = LpClient().trade_info(trade_id)
        if trade_info.status == TradeStatus.Complete:
            return True
        else:
            time.sleep(polling_interval_s)

    return False


def setup_inventory_account():
    inventory_account = get_account(account_name=INVENTORY_ACCOUNT_NAME)
    if inventory_account:
        return

    create_account(account_name=INVENTORY_ACCOUNT_NAME)

    currency_pairs = [
        CurrencyPairs[f"{Currency.Coin1}_{INVENTORY_COVER_CURRENCY}"],
    ]

    for currency_pair in currency_pairs:
        retries = 10
        polling_interval_s = 2

        for _ in range(retries):
            try:
                buy_funds(currency_pair)

            except Exception as e:
                logger.exception("trade and execute quote failed")
                time.sleep(polling_interval_s)


def buy_funds(currency_pair):
    quote = LpClient().get_quote(pair=currency_pair.value, amount=INVENTORY_AMOUNT)

    internal_address = get_inventory_deposit_address()

    trade_id = LpClient().trade_and_execute(
        quote_id=quote.quote_id,
        direction=Direction.Buy,
        diem_deposit_address=internal_address,
    )

    if wait_for_trade_to_complete(trade_id):
        return


def cover_order(order: Order):
    base_currency = Currency[order.base_currency]

    quote = LpClient().get_quote(
        CurrencyPair(base=base_currency, quote=INVENTORY_COVER_CURRENCY),
        amount=order.amount,
    )

    update_order(
        order_id=OrderId(UUID(order.id)),
        quote_id=str(quote.quote_id),
        quote_expiration=quote.expires_at,
        rate=quote.rate.rate,
        cover_status=CoverStatus.PendingCoverWithQuote,
    )

    covered = False
    if Direction[order.direction] == Direction.Sell:
        covered = _cover_sell(order, quote)

    elif Direction[order.direction] == Direction.Buy:
        covered = _cover_buy(order, quote)

    if covered:
        update_order(order_id=OrderId(UUID(order.id)), cover_status=CoverStatus.Covered)


def _cover_buy(order: Order, quote: QuoteData) -> bool:
    deposit_address = get_inventory_deposit_address()
    trade_id = LpClient().trade_and_execute(
        quote_id=quote.quote_id,
        direction=Direction[order.direction],
        diem_deposit_address=deposit_address,
    )
    trade_info = _wait_for_trade(order=order, trade_id=trade_id)

    if not trade_info:
        update_order(
            order_id=OrderId(UUID(order.id)),
            cover_status=CoverStatus.FailedCoverLPTradeError,
        )
        return False

    update_order(
        order_id=OrderId(UUID(order.id)),
        cover_status=CoverStatus.PendingCoverValidation,
    )

    vasp_address, internal_subaddress = decode_account(
        deposit_address, context.get().config.diem_address_hrp()
    )
    if not _validate_blockchain_transaction(
        blockchain_version=trade_info.tx_version,
        vasp_address=utils.account_address_hex(vasp_address),
        internal_subaddress=internal_subaddress.hex(),
        amount=round(trade_info.amount),
    ):
        update_order(
            order_id=OrderId(UUID(order.id)),
            cover_status=CoverStatus.FailedCoverTransactionError,
        )
        return False

    return True


def _cover_sell(order: Order, quote: QuoteData) -> bool:
    transfer_to_lp_blockchain_version = _transfer_funds_to_lp(order)

    if transfer_to_lp_blockchain_version == -1:
        update_order(
            order_id=OrderId(UUID(order.id)),
            cover_status=CoverStatus.FailedCoverTransactionError,
        )
        return False

    trade_info = LpClient().trade_and_execute(
        quote_id=quote.quote_id,
        direction=Direction[order.direction],
        tx_version=transfer_to_lp_blockchain_version,
    )

    if not trade_info:
        update_order(
            order_id=OrderId(UUID(order.id)),
            cover_status=CoverStatus.FailedCoverLPTradeError,
        )
        return False

    return True


def _transfer_funds_to_lp(order: Order) -> int:
    lp_details = LpClient().lp_details()
    inventory_account = get_account(account_name=INVENTORY_ACCOUNT_NAME).id

    tx = send_transaction(
        sender_id=inventory_account,
        amount=order.amount,
        currency=DiemCurrency[order.base_currency],
        destination_address=lp_details.vasp,
        destination_subaddress=lp_details.sub_address,
    )
    return _wait_for_lp_deposit_transaction_to_complete(tx.id)


def _wait_for_lp_deposit_transaction_to_complete(tx_id: int) -> int:
    retries = 10
    interval_s = 2
    for _ in range(retries):
        transaction = get_transaction(transaction_id=tx_id)
        if transaction.status == TransactionStatus.COMPLETED.value:
            try:
                return transaction.blockchain_version
            except Exception as e:
                log_execution(
                    f"Trade with LP failed, send transaction error, payment status {transaction.status}"
                )
                return -1
        time.sleep(interval_s)

    log_execution(f"Trade with LP failed, send transaction error, timeout")
    return -1


def _validate_blockchain_transaction(
    blockchain_version: int, vasp_address: str, internal_subaddress: str, amount: int
):
    retries = 10
    interval_s = 2
    for _ in range(retries):
        transaction = get_transaction(blockchain_version=blockchain_version)
        if transaction:
            if (
                transaction.status == TransactionStatus.COMPLETED.value
                and transaction.destination_address == vasp_address
                and transaction.destination_subaddress == internal_subaddress
                and transaction.amount == amount
            ):
                return transaction.blockchain_version
            else:
                log_execution(
                    f"Trade with LP failed, send transaction error, "
                    f"transaction status {transaction.status}, "
                    f"dest addr: {transaction.destination_address}"
                    f"dest subaddr: {transaction.destination_subaddress}"
                    f"amount: {transaction.amount}"
                )
                return -1
        time.sleep(interval_s)

    log_execution(f"Trade with LP failed, send transaction error, timeout")
    return -1


def _wait_for_trade(order: Order, trade_id: TradeId) -> Optional[TradeData]:
    retries = 10
    polling_interval_s = 2

    for _ in range(retries):
        trade_info = LpClient().trade_info(trade_id)
        if trade_info.status == TradeStatus.Complete:
            return trade_info

        time.sleep(polling_interval_s)

    return None


def get_inventory_deposit_address():
    return get_deposit_address(account_name=INVENTORY_ACCOUNT_NAME)
