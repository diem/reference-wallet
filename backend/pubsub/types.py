# pyre-strict

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra import libra_types, jsonrpc


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
        self.version = version
        self.sequence = sequence

        # The metadata deserializer is totally a prickly drama queen
        # It breaks on data directly from the blockchain without saying much
        self.metadata = libra_types.Metadata__Undefined()
        try:
            self.metadata = libra_types.Metadata.lcs_deserialize(metadata)
        except:
            pass

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
