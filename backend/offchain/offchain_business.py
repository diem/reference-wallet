# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from offchainapi.business import (
    BusinessContext,
    BusinessForceAbort,
    BusinessValidationFailure,
)

from offchainapi.crypto import ComplianceKey
from offchainapi.errors import OffChainErrorCode
from offchainapi.libra_address import LibraAddress
from offchainapi.payment import KYCData, PaymentActor, PaymentObject
from offchainapi.status_logic import Status

from wallet.storage.account import is_subaddress_exists, get_account_id_from_subaddr
from wallet.storage.transaction import (
    get_transaction_id_from_reference_id,
    get_single_transaction,
    update_transaction,
    get_transaction_status,
    add_transaction,
    add_metadata_signature,
)
from wallet.storage.user import get_user_by_account_id
from wallet.services.kyc import get_user_kyc_info, get_additional_user_kyc_info
from wallet.services.transaction import start_settle_offchain
from wallet.types import TransactionType, TransactionStatus
from diem_utils.types.currencies import DiemCurrency
import logging

from context import Context

logger = logging.getLogger(__name__)


def actor_to_libra_address(actor: PaymentActor) -> LibraAddress:
    return LibraAddress.from_encoded_str(actor.address)


class LRW(BusinessContext):
    def __init__(self, context: Context):
        self.vasp_address = context.config.vasp_diem_address()
        self.context = context

    def user_address(self, user_subaddress_hex: str) -> LibraAddress:
        return LibraAddress.from_hex(
            self.context.config.diem_address_hrp(),
            self.vasp_address.get_onchain_address_hex(),
            user_subaddress_hex,
        )

    def get_my_address(self):
        """Returns this VASP's str Diem address encoded in bech32"""
        return self.vasp_address.as_str()

    def open_channel_to(self, other_vasp_info):
        return True

    # ----- Actors -----

    def is_sender(self, payment: PaymentObject, ctx=None):
        """Returns true if the VASP is the sender of a payment.
        Returns:
            bool: Whether the VASP is the sender of the payment.
        """

        sender_address = actor_to_libra_address(payment.sender)
        return (
            self.vasp_address.onchain_address_bytes
            == sender_address.onchain_address_bytes
        )

    def is_recipient(self, payment: PaymentObject, ctx=None):
        """ Returns true if the VASP is the recipient of a payment.
        Returns:
            bool: Whether the VASP is the recipient of the payment.
        """
        return not self.is_sender(payment)

    async def check_account_existence(self, payment: PaymentObject, ctx=None):
        """ Checks that the actor (sub-account / sub-address) on this VASP
            exists. This may be either the recipient or the sender, since VASPs
            can initiate payments in both directions. If not throw an exception.
        Raises:
            BusinessValidationFailure: If the account does not exist.
        """
        actor = payment.sender if self.is_sender(payment) else payment.receiver

        subaddr = actor_to_libra_address(actor).get_subaddress_hex()
        if not is_subaddress_exists(subaddr):
            raise BusinessValidationFailure("unknown sub-address: {subaddr}")

    # ----- VASP Signature -----

    def validate_recipient_signature(self, payment: PaymentObject, ctx=None):
        """ Validates the recipient signature is correct. Raise an
            exception if the signature is invalid or not present.
            If the signature is valid do nothing.
        Raises:
            BusinessValidationFailure: If the signature is invalid
                    or not present.
        """

        sig = payment.recipient_signature

        try:
            # find receiver compliance public key
            compliance_key = self.context.get_vasp_public_compliance_key(
                actor_to_libra_address(payment.receiver).get_onchain_address_hex()
            )
            sender_address_bytes = actor_to_libra_address(
                payment.sender
            ).onchain_address_bytes
            compliance_key.verify_dual_attestation_data(
                payment.reference_id,
                sender_address_bytes,
                payment.action.amount,
                bytes.fromhex(sig),
            )
        except Exception as e:
            logger.exception("validate sig failed")
            raise BusinessValidationFailure(
                f"Could not validate recipient signature LRW: {e}"
            )

    async def get_recipient_signature(self, payment: PaymentObject, ctx=None) -> str:
        """ Gets a recipient signature on the payment ID."""

        # as a receiver, create metadata and sig with:
        # 1. sender address
        # 2. reference id
        # 3. amount
        sender_address_bytes = actor_to_libra_address(
            payment.sender
        ).onchain_address_bytes
        signed = self.context.config.offchain_compliance_key().sign_dual_attestation_data(
            payment.reference_id, sender_address_bytes, payment.action.amount,
        )
        return bytes.hex(signed)

    # ----- KYC/Compliance checks -----

    async def next_kyc_to_provide(self, payment: PaymentObject, ctx=None):
        """ Returns the level of kyc to provide to the other VASP based on its
            status. Can provide more if deemed necessary or less.
            Returns:
                Status: A set of status indicating to level of kyc to provide,
                that can include:
                    - `status_logic.Status.needs_kyc_data`
                    - `status_logic.Status.needs_recipient_signature`
            An empty set indicates no KYC should be provided at this moment.
            Raises:
                BusinessForceAbort : To abort the payment.
        """

        my_actor = payment.sender if self.is_sender(payment) else payment.receiver
        other_actor = payment.receiver if self.is_sender(payment) else payment.sender
        request = other_actor.status.as_status()

        kyc_data = set()
        if "kyc_data" not in my_actor.data:
            kyc_data.add(Status.needs_kyc_data)
        if self.is_recipient(payment) and "recipient_signature" not in payment.data:
            kyc_data.add(Status.needs_recipient_signature)

        if request == Status.needs_kyc_data and "kyc_data" not in other_actor.data:
            kyc_data.add(Status.needs_kyc_data)

        if request == Status.soft_match:
            kyc_data.add(Status.soft_match)

        if self.is_recipient(payment) and request == Status.needs_recipient_signature:
            kyc_data.add(Status.needs_recipient_signature)

        return kyc_data

    async def next_kyc_level_to_request(self, payment, ctx=None):
        """ Returns the next level of KYC to request from the other VASP. Must
            not request a level that is either already requested or provided.
            Args:
                payment (PaymentCommand): The concerned payment.
                ctx (Any): Optional context object that business can store custom data
            Returns:
                Status: Returns Status.none or the current status
                if no new information is required, otherwise a status
                code from:
                    - `status_logic.Status.needs_kyc_data`
                    - `status_logic.Status.needs_recipient_signature`
                    - `status_logic.soft_match`
                    - `status_logic.pending_review`
            Raises:
                BusinessForceAbort : To abort the payment.
        """

        my_actor = payment.sender if self.is_sender(payment) else payment.receiver
        other_actor = payment.receiver if self.is_sender(payment) else payment.sender

        if "kyc_data" not in other_actor.data:
            return Status.needs_kyc_data

        if self.is_sender(payment) and "recipient_signature" not in payment:
            return Status.needs_recipient_signature

        # TODO: check kyc data, decide to pending review or soft match

        return Status.none

    async def get_extended_kyc(self, payment: PaymentObject, ctx=None):
        """ Provides the extended KYC information for this payment.
            Raises:
                   BusinessNotAuthorized: If the other VASP is not authorized to
                    receive extended KYC data for this payment.
            Returns:
                KYCData: Returns the extended KYC information for
                this payment.
        """

        user_info = get_user_kyc_info(self.get_user_id(payment))

        return KYCData(user_info)

    async def get_additional_kyc(self, payment: PaymentObject, ctx=None):
        """ Provides the additional KYC information for this payment.
            The additional information is requested or may be provided in case
            of a `soft_match` state from the other VASP indicating more
            information is required to disambiguate an individual.
            Raises:
                   BusinessNotAuthorized: If the other VASP is not authorized to
                    receive extended KYC data for this payment.
            Returns:
                KYCData: Returns the extended KYC information for
                this payment.
        """

        user_info = get_additional_user_kyc_info(self.get_user_id(payment))
        return KYCData(user_info)

    # ----- Payment Processing -----

    async def payment_pre_processing(self, other_address, seq, command, payment):
        """ An async method to let VASP perform custom business logic to a
        successsful (sequenced & ACKed) command prior to normal processing.
        For example it can be used to check whether the payment is in terminal
        status. The command could have originated either from the other VASP
        or this VASP (see `command.origin` to determine this).
        Args:
            other_address (str): the encoded Diem Blockchain address of the other VASP.
            seq (int): the sequence number into the shared command sequence.
            command (ProtocolCommand): the command that lead to the new or
                updated payment.
            payment (PaymentObject): the payment resulting from this command.
        Returns None or a context objext that will be passed on the
        other business context functions.
        """

        if (
            payment.sender.status.as_status() == Status.ready_for_settlement
            and payment.receiver.status.as_status() == Status.ready_for_settlement
        ):
            if self.is_sender(payment):
                ref_id = payment.reference_id
                transaction_id = get_transaction_id_from_reference_id(ref_id)
                transaction = get_single_transaction(transaction_id)
                add_metadata_signature(ref_id, payment.recipient_signature)

                if transaction.status == TransactionStatus.COMPLETED:
                    return None
                if transaction.status == TransactionStatus.READY_FOR_ON_CHAIN:
                    start_settle_offchain(transaction_id=transaction.id)

                # TODO: What should happen in this case?
                if transaction.status == TransactionStatus.CANCELED:
                    raise ValueError("what should happen in this case?")

            else:
                receiver_subaddress = LibraAddress.from_encoded_str(
                    payment.receiver.address
                ).get_subaddress_hex()
                txn_id = add_transaction(
                    amount=payment.action.amount,
                    currency=DiemCurrency(payment.action.currency),
                    payment_type=TransactionType.OFFCHAIN,
                    status=TransactionStatus.READY_FOR_ON_CHAIN,
                    source_id=None,
                    source_address=LibraAddress.from_encoded_str(
                        payment.sender.address
                    ).get_onchain_address_hex(),
                    source_subaddress=LibraAddress.from_encoded_str(
                        payment.sender.address
                    ).get_subaddress_hex(),
                    destination_id=get_account_id_from_subaddr(receiver_subaddress),
                    destination_address=LibraAddress.from_encoded_str(
                        payment.receiver.address
                    ).get_onchain_address_hex(),
                    destination_subaddress=receiver_subaddress,
                    sequence=None,
                    blockchain_version=None,
                    reference_id=payment.reference_id,
                    metadata_signature=payment.recipient_signature,
                )

    # ----- Settlement -----

    async def ready_for_settlement(self, payment, ctx=None):
        """ Indicates whether a payment is ready for settlement as far as this
            VASP is concerned. Once it returns True it must never return False.
            In particular it **must** check that:
                - Accounts exist and have the funds necessary.
                - Sender of funds intends to perform the payment (VASPs can
                  initiate payments from an account on the other VASP.)
                - KYC information provided **on both sides** is correct and to
                  the VASPs satisfaction. On payment creation a VASP may suggest
                  KYC information on both sides.
            If all the above are true, then return `True`.
            If any of the above are untrue throw an BusinessForceAbort.
            If any more KYC is necessary then return `False`.
            This acts as the finality barrier and last check for this VASP.
            After this call returns True this VASP can no more abort the
            payment (unless the other VASP aborts it).
            Args:
                payment (PaymentCommand): The concerned payment.
            Raises:
                BusinessForceAbort: If any of the above condutions are untrue.
            Returns:
                bool: Whether the VASP is ready to settle the payment.
            """

        my_role = self.get_my_role(payment)
        other_role = self.get_other_role(payment)

        if (
            "kyc_data" not in payment.data[other_role]
            or "kyc_data" not in payment.data[my_role]
        ):
            return False

        # This VASP always settles payments on chain, so we always need
        # a signature to settle on chain.
        if "recipient_signature" not in payment:
            return False

        need_to_kyc = await self.next_kyc_level_to_request(payment)
        if need_to_kyc is not Status.none:
            return False

        if my_role == "sender":
            reference_id = payment.reference_id
            transaction_id = get_transaction_id_from_reference_id(reference_id)

            if transaction_id is None:
                raise BusinessForceAbort(
                    OffChainErrorCode.payment_vasp_error,
                    f"Transaction ID could not be found in vasp {my_role}",
                )

            if (
                not get_transaction_status(transaction_id)
                == TransactionStatus.OFF_CHAIN_STARTED
            ):
                raise BusinessForceAbort(
                    OffChainErrorCode.payment_vasp_error,
                    f"Transaction has wrong status {get_transaction_status(transaction_id)}",
                )

            update_transaction(
                transaction_id=transaction_id,
                status=TransactionStatus.READY_FOR_ON_CHAIN,
            )
        return True

    # the followings are non interface util functions

    def get_my_role(self, payment) -> str:
        return "sender" if self.is_sender(payment) else "receiver"

    def get_other_role(self, payment) -> str:
        return "receiver" if self.is_sender(payment) else "sender"

    def get_account_id(self, payment) -> int:
        my_actor = payment.sender if self.is_sender(payment) else payment.receiver
        address = LibraAddress.from_encoded_str(my_actor.address)
        subaddress = address.get_subaddress_hex()
        account_id = get_account_id_from_subaddr(subaddress)
        if account_id is None:
            role = self.get_my_role(payment)
            raise BusinessForceAbort(
                OffChainErrorCode.payment_invalid_libra_subaddress,
                f"Subaccount {subaddress} does not exist in {role}.",
            )
        return account_id

    def get_user_id(self, payment) -> int:
        return get_user_by_account_id(self.get_account_id(payment)).id
