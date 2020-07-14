# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from pubsub_proxy.events import PubSubEvent
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
    def fromPubSubEvent(cls, pubsub_event: PubSubEvent) -> "LRWPubSubEvent":
        return LRWPubSubEvent(
            sender=pubsub_event.payer.hex(),
            receiver=pubsub_event.payee.hex(),
            amount=pubsub_event.amount,
            currency=pubsub_event.currency,
            metadata=pubsub_event.subaddress,  # NOTE: pubsub proxy based on old metadata spec
            version=pubsub_event.transaction_version,
            sequence=pubsub_event.sequence_number,
        )

    def __str__(self) -> str:
        """
        Print as a nested dict to str
        """
        d = self.__dict__.copy()
        d["metadata"] = self.metadata.__dict__
        return str(d)
