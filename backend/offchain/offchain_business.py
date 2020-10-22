# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from offchainapi.business import (
    BusinessContext,
    BusinessForceAbort,
    BusinessValidationFailure,
)
from offchainapi.payment import KYCData
from offchainapi.status_logic import Status
from offchainapi.libra_address import LibraAddress
from offchainapi.crypto import ComplianceKey
from offchainapi.errors import OffChainErrorCode
from libra import jsonrpc
from wallet.storage.account import is_subaddress_exists, get_account_id_from_subaddr
from wallet.storage.transaction import (
    get_transaction_id_from_reference_id,
    get_single_transaction,
    update_transaction,
    get_transaction_status,
    add_transaction,
)
from wallet.storage.user import get_user_by_account_id
from wallet.services.kyc import get_user_kyc_info, get_additional_user_kyc_info
from wallet.services.transaction import submit_onchain, start_settle_offchain
from wallet.services import run_bg_tasks
from wallet.types import TransactionType, TransactionStatus
from libra_utils.types.currencies import LibraCurrency

import logging

logger = logging.getLogger(name="lrw_offchain_business")
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class VASPInfoNotFoundException(Exception):
    pass


class BaseURLNotFoundException(Exception):
    pass


class ComplianceKeyNotFoundException(Exception):
    pass


def get_compliance_key_on_chain(addr: str) -> ComplianceKey:
    JSON_RPC_URL = os.getenv("JSON_RPC_URL", "https://testnet.libra.org/v1")
    client = jsonrpc.Client(JSON_RPC_URL)
    account = client.get_account(addr)
    if account is None:
        raise VASPInfoNotFoundException(f"VASP account {addr} was not found onchain")

    role = account.role
    compliance_key: str = role.compliance_key
    logger.info(f"~~~~~~~~~got compliance key {compliance_key}")

    if not compliance_key:
        raise BaseURLNotFoundException(f"Compliance Key is empty for peer vasp {addr}")

    key = ComplianceKey.from_pub_bytes(bytes.fromhex(compliance_key))
    logger.info(f"~~~~~~~~~got compliance key full {key}")
    assert not key._key.has_private
    return key


class LRWOffChainBusinessContext(BusinessContext):
    def __init__(self, my_addr, reliable=True):
        self.my_addr = my_addr

        # Option to make the contect unreliable to help test error handling.
        self.reliable = reliable
        self.reliable_count = 0

    def cause_error(self):
        self.reliable_count += 1
        fail = self.reliable_count % 5 == 0
        if fail:
            e = BusinessValidationFailure(
                "Artifical error caused for " "testing error handling"
            )
            raise e

    def open_channel_to(self, other_vasp_info):
        """Requests authorization to open a channel to another VASP.
        If it is authorized nothing is returned. If not an exception is
        raised.
        Args:
            other_vasp_info (LibraAddress): The Libra Blockchain address of the other VASP.
        Raises:
            BusinessNotAuthorized: If the current VASP is not authorised
                    to connect with the other VASP.
        """
        return True

    # ----- Actors -----

    def is_sender(self, payment, ctx=None):
        """Returns true if the VASP is the sender of a payment.
        Args:
            payment (PaymentCommand): The concerned payment.
            ctx (Any): Optional context object that business can store custom data
        Returns:
            bool: Whether the VASP is the sender of the payment.
        """
        return self.my_addr.as_str() == payment.sender.get_onchain_address_encoded_str()

    def is_recipient(self, payment, ctx=None):
        """ Returns true if the VASP is the recipient of a payment.
        Args:
            payment (PaymentCommand): The concerned payment.
            ctx (Any): Optional context object that business can store custom data
        Returns:
            bool: Whether the VASP is the recipient of the payment.
        """
        return not self.is_sender(payment)

    async def check_account_existence(self, payment, ctx=None):
        """ Checks that the actor (sub-account / sub-address) on this VASP
            exists. This may be either the recipient or the sender, since VASPs
            can initiate payments in both directions. If not throw an exception.
        Args:
            payment (PaymentCommand): The payment command containing the actors
                to check.
            ctx (Any): Optional context object that business can store custom data
        Raises:
            BusinessValidationFailure: If the account does not exist.
        """
        logger.info(
            f"~~~~~~~~~~~LRW check_account_existence~~~~~~~~~~~~{LibraAddress.from_encoded_str(payment.sender.address).get_subaddress_hex()}"
        )
        if self.is_sender(payment):
            subaddr = LibraAddress.from_encoded_str(
                payment.sender.address
            ).get_subaddress_hex()
        else:
            subaddr = LibraAddress.from_encoded_str(
                payment.receiver.address
            ).get_subaddress_hex()

        if is_subaddress_exists(subaddr):
            print("=========================SUBADDRESSE XITS?")
            return
        print("=========================SUBADDRESSE DOESN'T EIST")
        raise BusinessValidationFailure("Subaccount does not exist.")

    # ----- VASP Signature -----

    def validate_recipient_signature(self, payment, ctx=None):
        """ Validates the recipient signature is correct. Raise an
            exception if the signature is invalid or not present.
            If the signature is valid do nothing.
        Args:
            payment (PaymentCommand): The payment command containing the
                signature to check.
            ctx (Any): Optional context object that business can store custom data
        Raises:
            BusinessValidationFailure: If the signature is invalid
                    or not present.
        """
        logger.info("~~~~~~~~~~~111111111validate_recipient_signature LRW~~~~~~~~~~~")
        if "recipient_signature" in payment.data:
            try:
                recipient_addr = LibraAddress.from_encoded_str(
                    payment.receiver.address
                ).get_onchain_address_hex()
                libra_address_hex = LibraAddress.from_encoded_str(
                    payment.sender.address
                ).get_onchain_address_hex()
                logger.info(
                    f"~~~~~~~~~~~libra_address_hex LRW~~~~~~~~~~{libra_address_hex}~"
                )
                libra_address_bytes = bytes.fromhex(libra_address_hex)
                logger.info(
                    f"~~~~~~~~~~~libra_address_bytes LRW~~~~~~~~~~{libra_address_bytes}~"
                )
                sig = payment.recipient_signature
                compliance_key = get_compliance_key_on_chain(recipient_addr)
                logger.info(
                    f"~~~~~~~~~~~got comp key {compliance_key.export_pub()}~~~~~~~~~~~~"
                )
                compliance_key.verify_dual_attestation_data(
                    payment.reference_id,
                    libra_address_bytes,
                    payment.action.amount,
                    bytes.fromhex(sig),
                )

                if not self.reliable:
                    self.cause_error()

                logger.info("----------valid recipient signature=======")
                return
            except Exception as e:
                raise BusinessValidationFailure(
                    f"Could not validate recipient signature LRW: {e}"
                )

        sig = payment.data.get("recipient_signature", "Not present")
        raise BusinessValidationFailure(f"Invalid signature: {sig}")

    async def get_recipient_signature(self, payment, ctx=None):
        """ Gets a recipient signature on the payment ID.
        Args:
            payment (PaymentCommand): The payment to sign.
            ctx (Any): Optional context object that business can store custom data
        """
        from . import LRW_VASP_COMPLIANCE_KEY

        logger.info("~~~~~~~~~~~1111111111get_recipient_signature~~~~~~~~~~~~~")
        libra_address_bytes = LibraAddress.from_encoded_str(
            payment.sender.address
        ).onchain_address_bytes
        signed = LRW_VASP_COMPLIANCE_KEY.sign_dual_attestation_data(
            payment.reference_id, libra_address_bytes, payment.action.amount
        )
        logger.info(f"this SIGNATURE {bytes.hex(signed)}")
        return bytes.hex(signed)

    # ----- KYC/Compliance checks -----

    def get_my_role(self, payment):
        return ["receiver", "sender"][self.is_sender(payment)]

    def get_other_role(self, payment):
        return ["sender", "receiver"][self.is_sender(payment)]

    async def next_kyc_to_provide(self, payment, ctx=None):
        """ Returns the level of kyc to provide to the other VASP based on its
            status. Can provide more if deemed necessary or less.
            Args:
                payment (PaymentCommand): The concerned payment.
                ctx (Any): Optional context object that business can store custom data
            Returns:
                Status: A set of status indicating to level of kyc to provide,
                that can include:
                    - `status_logic.Status.needs_kyc_data`
                    - `status_logic.Status.needs_recipient_signature`
            An empty set indicates no KYC should be provided at this moment.
            Raises:
                BusinessForceAbort : To abort the payment.
        """
        logger.info("~~~~~~~~~~~next_kyc_to_provide~~~~~~~~~~~")
        role = self.get_my_role(payment)
        other_role = self.get_other_role(payment)
        actor = payment.data[role]
        other_actor = payment.data[other_role]
        kyc_data = set()

        if "kyc_data" not in actor:
            logger.info("~~~~~~~~~~~next_kyc_to_provide need kyc data~~~~~~~~~~~")
            kyc_data.add(Status.needs_kyc_data)

        if payment.data[other_role].status.as_status() == Status.needs_kyc_data:
            logger.info("~~~~~~~~~~~next_kyc_to_provide need kyc data 2~~~~~~~~~~~")
            kyc_data.add(Status.needs_kyc_data)

        if (
            "additional_kyc_data" not in actor
            and other_actor.status.as_status() == Status.soft_match
        ):
            logger.info(
                "~~~~~~~~~~~next_kyc_to_provide need additional data~~~~~~~~~~~"
            )
            kyc_data.add(Status.soft_match)

        if role == "receiver" and "recipient_signature" not in payment:
            logger.info(
                "~~~~~~~~~~~next_kyc_to_provide need recipient signature~~~~~~~~~~~"
            )
            kyc_data.add(Status.needs_recipient_signature)
        logger.info("~~~~~~~~~~~~~~~~next_kyc_level_to_provide reached end~~~~~~~~~~~")

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
        logger.info("~~~~~~~~~~~next_kyc_level_to_request~~~~~~~~~~~")
        other_role = self.get_other_role(payment)
        other_actor = payment.data[other_role]
        if "kyc_data" not in other_actor:
            logger.info(
                "~~~~~~~~~~~next_kyc_level_to_request needs kyc data~~~~~~~~~~~"
            )
            return Status.needs_kyc_data

        if "additional_kyc_data" not in other_actor:
            logger.info("~~~~~~~~~~~next_kyc_level_to_request soft match~~~~~~~~~~~")
            return Status.soft_match

        if other_role == "receiver" and "recipient_signature" not in payment:
            logger.info(
                "~~~~~~~~~~~next_kyc_level_to_request need recipient signature~~~~~~~~~~~"
            )
            return Status.needs_recipient_signature

        logger.info("~~~~~~~~~~~~~~~~next_kyc_level_to_request reached end~~~~~~~~~~~")

        return Status.none

    async def get_extended_kyc(self, payment, ctx=None):
        """ Provides the extended KYC information for this payment.
            Args:
                payment (PaymentCommand): The concerned payment.
                ctx (Any): Optional context object that business can store custom data
            Raises:
                   BusinessNotAuthorized: If the other VASP is not authorized to
                    receive extended KYC data for this payment.
            Returns:
                KYCData: Returns the extended KYC information for
                this payment.
        """
        logger.info("~~~~~~~~~~~get_extended_kyc~~~~~~~~~~~")

        role = self.get_my_role(payment)
        address = LibraAddress.from_encoded_str(payment.data[role].address)
        subaddress = address.get_subaddress_hex()
        account_id = get_account_id_from_subaddr(subaddress)
        if account_id is None:
            logger.debug("account does not exist!")
            raise BusinessForceAbort(
                OffChainErrorCode.payment_invalid_libra_subaddress,
                f"Subaccount {subaddress} does not exist in {role}.",
            )
        user_id = get_user_by_account_id(account_id).id
        user_info = get_user_kyc_info(user_id)
        logger.info(f"====user_info: {user_info}")
        return KYCData(user_info)

    async def get_additional_kyc(self, payment, ctx=None):
        """ Provides the additional KYC information for this payment.
            The additional information is requested or may be provided in case
            of a `soft_match` state from the other VASP indicating more
            information is required to disambiguate an individual.
            Args:
                payment (PaymentCommand): The concerned payment.
            Raises:
                   BusinessNotAuthorized: If the other VASP is not authorized to
                    receive extended KYC data for this payment.
            Returns:
                KYCData: Returns the extended KYC information for
                this payment.
        """
        logger.info("~~~~~~~~~~~get_additional_kyc~~~~~~~~~~~")

        role = self.get_my_role(payment)
        address = LibraAddress.from_encoded_str(payment.data[role].address)
        subaddress = address.get_subaddress_hex()
        account_id = get_account_id_from_subaddr(subaddress)
        logger.info(
            f"====address: {address}, subaddress: {subaddress}, account_id: {account_id}"
        )
        if account_id is None:
            logger.debug("account does not exist!")
            raise BusinessForceAbort(
                OffChainErrorCode.payment_invalid_libra_subaddress,
                f"Subaccount {subaddress} does not exist in {role}.",
            )
        user_id = get_user_by_account_id(account_id).id
        user_info = get_additional_user_kyc_info(user_id)
        logger.info(f"====user_info: {user_info}")
        return KYCData(user_info)

    # ----- Payment Processing -----

    async def payment_pre_processing(self, other_address, seq, command, payment):
        """ An async method to let VASP perform custom business logic to a
        successsful (sequenced & ACKed) command prior to normal processing.
        For example it can be used to check whether the payment is in terminal
        status. The command could have originated either from the other VASP
        or this VASP (see `command.origin` to determine this).
        Args:
            other_address (str): the encoded Libra Blockchain address of the other VASP.
            seq (int): the sequence number into the shared command sequence.
            command (ProtocolCommand): the command that lead to the new or
                updated payment.
            payment (PaymentObject): the payment resulting from this command.
        Returns None or a context objext that will be passed on the
        other business context functions.
        """
        logger.info(
            f"~~~~~~~~~~~~~~~~payment_pre_processing~~~~~~~~~~~{payment.sender.status.as_status()}, {payment.receiver.status.as_status()}"
        )
        if (
            payment.sender.status.as_status() == Status.ready_for_settlement
            and payment.receiver.status.as_status() == Status.ready_for_settlement
        ):
            if self.is_sender(payment):
                logger.info(
                    "~~~~~~~~~~~~~~~~SENDER pre both_ready_for_settlement~~~~~~~~~~~"
                )
                ref_id = payment.reference_id
                transaction_id = get_transaction_id_from_reference_id(ref_id)
                transaction = get_single_transaction(transaction_id)

                if transaction.status == TransactionStatus.COMPLETED:
                    return None
                if transaction.status == TransactionStatus.READY_FOR_ON_CHAIN:
                    logger.info(
                        f"~~~~~~~~~~need to run background tasks~~~~~~{run_bg_tasks()}"
                    )
                    start_settle_offchain(transaction_id=transaction.id)

                # TODO: What should happen in this case?
                if transaction.status == TransactionStatus.CANCELED:
                    logger.info("Ready for settlement but transactiono was canceled")

                logger.info(
                    "~~~~~~~~~~~~~~~~pre both_ready_for_settlement end~~~~~~~~~~~"
                )
            else:
                logger.info(
                    "~~~~~~~~~~~~~~~~RECEIVER pre both_ready_for_settlement~~~~~~~~~~~"
                )
                receiver_subaddress = LibraAddress.from_encoded_str(
                    payment.receiver.address
                ).get_subaddress_hex()
                txn_id = add_transaction(
                    amount=payment.action.amount,
                    currency=LibraCurrency(payment.action.currency),
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
                )
                logger.info(
                    f"~~~~~~~~~~~~~~~~RECEIVER pre both_ready_for_settlement done with txn id {txn_id}~~~~~~~~~~~"
                )

    async def payment_initial_processing(self, payment, ctx=None):
        """
        Allow business to do custom pre-processing to a payment
        Args:
            payment (PaymentObject): The concerned payment.
            ctx (Any): Optional context object that business can store custom data
        Raises:
            BusinessForceAbort: When business wants to abort a payment
        """
        logger.info("~~~~~~~~~~~~~~~~payment_initial_processing~~~~~~~~~~~")
        if (
            payment.sender.status.as_status() == Status.ready_for_settlement
            and payment.receiver.status.as_status() == Status.ready_for_settlement
        ):
            logger.info("~~~~~~~~~~~~~~~~initial both_ready_for_settlement~~~~~~~~~~~")

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
        if not self.reliable:
            self.cause_error()

        my_role = self.get_my_role(payment)
        other_role = self.get_other_role(payment)
        logger.info(f"~~~~~~~~~~~~~~~~ready_for_settlement~~~~~~~~~~~{my_role}")

        if (
            "kyc_data" not in payment.data[other_role]
            or "kyc_data" not in payment.data[my_role]
        ):
            logger.info("@@@kyc return false 1")
            return False

        # This VASP always settles payments on chain, so we always need
        # a signature to settle on chain.
        if "recipient_signature" not in payment:
            logger.info("@@@kyc return false 2")
            return False

        need_to_kyc = await self.next_kyc_level_to_request(payment)
        if need_to_kyc is not Status.none:
            logger.info("@@@kyc return false 3")
            return False

        logger.info("@@@kyc return passed   ")

        if my_role == "sender":
            logger.info("@@@kyc i am sender")
            reference_id = payment.reference_id
            transaction_id = get_transaction_id_from_reference_id(reference_id)

            if transaction_id is None:
                logger.info("@@@kyc transaction is is none")
                raise BusinessForceAbort(
                    OffChainErrorCode.payment_vasp_error,
                    f"Transaction ID could not be found in vasp {my_role}",
                )

            if (
                not get_transaction_status(transaction_id)
                == TransactionStatus.OFF_CHAIN_STARTED
            ):
                logger.info("@@@kyc in wrong state")
                raise BusinessForceAbort(
                    OffChainErrorCode.payment_vasp_error,
                    f"Transaction has wrong status {get_transaction_status(transaction_id)}",
                )

            update_transaction(
                transaction_id=transaction_id,
                status=TransactionStatus.READY_FOR_ON_CHAIN,
            )
        logger.info("@@@kyc ready to settle")
        return True
