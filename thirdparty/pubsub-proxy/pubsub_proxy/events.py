#!/usr/bin/env python3
from typing import Any, Dict, Optional

import pylibra

from .util import transform_address


class PubSubEvent:
    def __init__(
        self, event: pylibra.PaymentEvent, event_key: Optional[str] = None
    ) -> None:
        self.payer: bytes = event.sender_address
        self.payee: bytes = event.receiver_address
        self.amount = event.amount
        self.currency = event.currency
        self.subaddress = event.metadata
        self.event_type = "sent" if event.is_sent else "received"
        # TODO: set timestamp
        self.timestamp = 0
        self.event_key = event_key
        # TODO: replace hacky hardcode after pylibra update
        self.transaction_version = event.__dict__["_ev_dict"]["transaction_version"]
        self.sequence_number = event.__dict__["_ev_dict"]["sequence_number"]

    @property
    def sender(self) -> bytes:
        return self.payer if self.event_type == "sent" else self.payee

    @property
    def message(self) -> Dict[str, Any]:
        return {
            "transaction_version": self.transaction_version,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "amount": self.amount,
            "payee": transform_address(self.payee),
            "payer": transform_address(self.payer),
            "subaddress": transform_address(self.subaddress),
        }
