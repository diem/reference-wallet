# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from time import sleep

import dramatiq

from pubsub.types import LRWPubSubEvent
from wallet.services.order import (
    execute_order,
    cover_order,
)
from .utils import retry
from ..logging import debug_log, log_execution
from ..services.kyc import verify_kyc
from ..services.transaction import (
    submit_onchain,
    process_incoming_transaction,
    settle_offchain,
)
from diem_utils.types.currencies import DiemCurrency

TIME_BEFORE_KYC_APPROVAL = 5


@dramatiq.actor(store_results=True)
@debug_log(None)
def async_start_kyc(user_id: int) -> None:
    sys.stdout.write("hhhhhhhhh")
    log_execution("Enter async_start_kyc")
    sleep(TIME_BEFORE_KYC_APPROVAL)
    verify_kyc(user_id)


@dramatiq.actor(store_results=True)
@debug_log(None)
def async_execute_order(order_id, payment_method) -> None:
    log_execution("Enter async_execute_order")
    execute_order(order_id, payment_method)


@dramatiq.actor(store_results=True)
@debug_log(None)
def async_cover_order(order_id) -> None:
    log_execution("Enter async_cover")
    cover_order(order_id)


@dramatiq.actor(store_results=True)
@debug_log(None)
def async_external_transaction(transaction_id: int) -> None:
    log_execution("Enter async_external_transaction")
    submit_onchain(transaction_id=transaction_id)


@dramatiq.actor(store_results=True)
@debug_log(None)
def async_external_transaction_offchain(transaction_id: int) -> None:
    log_execution("Enter async_external_transaction_offchain")
    settle_offchain(transaction_id=transaction_id)


@dramatiq.actor(store_results=True)
@retry(Exception, delay=1)
def process_incoming_txn(txn: LRWPubSubEvent) -> None:
    metadata = txn.metadata
    blockchain_version = txn.version
    sender_address = txn.sender
    receiver_address = txn.receiver
    sequence = txn.sequence
    amount = txn.amount
    currency = DiemCurrency[txn.currency]
    process_incoming_transaction(
        blockchain_version=blockchain_version,
        sender_address=sender_address,
        receiver_address=receiver_address,
        sequence=sequence,
        amount=amount,
        currency=currency,
        metadata=metadata,
    )
