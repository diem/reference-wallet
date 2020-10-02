# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra import libra_types, jsonrpc
from libra_utils.libra import TransactionMetadata


class LRWPubSubEvent:
    def __init__(
        self,
        sender: str,
        receiver: str,
        amount: int,
        currency: str,
        metadata: bytes,
        version: int,
        sequence: int,
    ) -> None:
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.currency = currency
        self.metadata: TransactionMetadata = TransactionMetadata.from_bytes(metadata)
        self.version = version
        self.sequence = sequence

    @classmethod
    def from_jsonrpc_event(cls, event: jsonrpc.Event) -> "LRWPubSubEvent":
        return LRWPubSubEvent(
            sender=event.data.sender,
            receiver=event.data.receiver,
            amount=event.data.amount.amount,
            currency=event.data.amount.currency,
            metadata=bytes.fromhex(event.data.metadata),
            version=event.transaction_version,
            sequence=event.sequence_number,
        )

    def __str__(self) -> str:
        """
        Print as a nested dict to str
        """
        d = self.__dict__.copy()
        d["metadata"] = self.metadata.__dict__
        return str(d)
