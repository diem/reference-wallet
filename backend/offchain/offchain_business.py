# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from offchainapi.business import (
    BusinessContext,
    BusinessForceAbort,
    BusinessValidationFailure,
)
from offchainapi.payment import KYCData
from wallet.types import TransactionStatus
from offchainapi.status_logic import Status
from offchainapi.libra_address import LibraAddress
from wallet.storage.account import is_subaddress_exists, get_account_id_from_subaddr
from wallet.storage.transaction import (
    get_transaction_id_from_reference_id,
    get_single_transaction,
    update_transaction,
    get_transaction_status,
)
from wallet.storage.user import get_user_by_account_id
from wallet.services.kyc import get_user_kyc_info
from wallet.services.transaction import submit_onchain, start_settle_offchain
from wallet.services import run_bg_tasks
from wallet.logging import log_execution


logger = logging.getLogger(name="lrw_offchain_business")


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
        return True

    # ----- Actors -----

    def is_sender(self, payment, ctx=None):
        return self.my_addr.as_str() == payment.sender.get_onchain_address_encoded_str()

    def is_recipient(self, payment, ctx=None):
        return not self.is_sender(payment)

    async def check_account_existence(self, payment, ctx=None):
        logger.info(
            "~~~~~~~~~~~LRW check_account_existence~~~~~~~~~~~~",
            LibraAddress(payment.sender.address).get_subaddress_bytes().hex(),
        )
        log_execution(
            "~~~~~~~~~~~LRW check_account_existence~~~~~~~~~~~~",
            LibraAddress(payment.sender.address).get_subaddress_bytes().hex(),
        )
        if self.is_sender(payment):
            subaddr = LibraAddress(payment.sender.address).get_subaddress_bytes().hex()
        else:
            subaddr = (
                LibraAddress(payment.receiver.address).get_subaddress_bytes().hex()
            )

        if is_subaddress_exists(subaddr):
            print("=========================SUBADDRESSE XITS?")
            return
        print("=========================SUBADDRESSE DOESN'T EIST")
        raise BusinessValidationFailure("Subaccount does not exist.")

    # ----- VASP Signature -----

    def get_peer_keys(self):
        from . import peer_keys
        log_execution("~~~~~~~~~~~get_peer_keys~~~~~~~~~~~")
        return peer_keys

    def validate_recipient_signature(self, payment, ctx=None):
        logger.info("~~~~~~~~~~~validate_recipient_signature~~~~~~~~~~~")
        log_execution("~~~~~~~~~~~validate_recipient_signature~~~~~~~~~~~")
        if "recipient_signature" in payment.data:
            peer_keys = self.get_peer_keys()

            try:
                recipient_addr = payment.receiver.get_onchain_address_encoded_str()
                reference_id_bytes = str.encode(payment.reference_id)
                libra_address_bytes = LibraAddress.from_encoded_str(
                    payment.sender.address
                ).onchain_address_bytes
                sig = payment.data["recipient_signature"]
                peer_keys[recipient_addr].verify_ref_id(
                    reference_id_bytes, libra_address_bytes, payment.action.amount, sig
                )

                if not self.reliable:
                    self.cause_error()

                logger.info("----------valid recipient signature=======")
                return
            except Exception as e:
                raise BusinessValidationFailure(
                    f"Could not validate recipient signature: {sig}, {e}"
                )

        sig = payment.data.get("recipient_signature", "Not present")
        raise BusinessValidationFailure(f"Invalid signature: {sig}")

    async def get_recipient_signature(self, payment, ctx=None):
        from . import LRW_VASP_COMPLIANCE_KEY

        logger.info("~~~~~~~~~~~get_recipient_signature~~~~~~~~~~~~~")
        reference_id_bytes = str.encode(payment.reference_id)
        libra_addres = LibraAddress.from_encoded_str(
            payment.sender.address
        ).onchain_address_bytes
        signed = LRW_VASP_COMPLIANCE_KEY.sign_ref_id(
            reference_id_bytes, libra_addres, payment.action.amount
        )
        logger.info(f"this SIGNATURE {signed}")
        return signed

    # ----- KYC/Compliance checks -----

    def get_my_role(self, payment):
        return ["receiver", "sender"][self.is_sender(payment)]

    def get_other_role(self, payment):
        return ["sender", "receiver"][self.is_sender(payment)]

    async def next_kyc_to_provide(self, payment, ctx=None):
        logger.info("~~~~~~~~~~~next_kyc_to_provide~~~~~~~~~~~")
        log_execution("~~~~~~~~~~~next_kyc_to_provide~~~~~~~~~~~")
        role = self.get_my_role(payment)
        other_role = self.get_other_role(payment)
        actor = payment.data[role]
        kyc_data = set()

        if "kyc_data" not in actor:
            kyc_data.add(Status.needs_kyc_data)

        if payment.data[other_role].status.as_status() == Status.needs_kyc_data:
            kyc_data.add(Status.needs_kyc_data)

        if (
            payment.data[other_role].status.as_status()
            == Status.needs_recipient_signature
        ):
            if role == "receiver":
                kyc_data.add(Status.needs_recipient_signature)

        return kyc_data

    async def next_kyc_level_to_request(self, payment, ctx=None):
        logger.info("~~~~~~~~~~~next_kyc_level_to_request~~~~~~~~~~~")
        log_execution("~~~~~~~~~~~next_kyc_level_to_request~~~~~~~~~~~")
        other_role = self.get_other_role(payment)
        other_actor = payment.data[other_role]
        if "kyc_data" not in other_actor:
            return Status.needs_kyc_data

        if other_role == "receiver" and "recipient_signature" not in payment:
            return Status.needs_recipient_signature

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
        logger.info(f"address: {address}")
        subaddress = address.get_subaddress_hex()
        logger.info(f"subaddress: {subaddress}")
        account_id = get_account_id_from_subaddr(subaddress)
        logger.info(f"====account_id: {account_id}")
        if account_id is None:
            logger.debug("account does not exist!")
            raise BusinessForceAbort(
                f"Could not verify subaddress {subaddress} belongs to {role}"
            )
        user_id = get_user_by_account_id(account_id).id
        logger.info(f"====user_id: {user_id}")
        # TODO: confirm how to format kyc data
        user_info = get_user_kyc_info(user_id)
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
            other_address (str): the encoded libra address of the other VASP.
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
            logger.info("~~~~~~~~~~~~~~~~now they're ready~~~~~~~~~~~")
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
                print("What should happen in this case?")

            logger.info("~~~~~~~~~~~~~~~~pre both_ready_for_settlement~~~~~~~~~~~")

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
        if not self.reliable:
            self.cause_error()

        my_role = self.get_my_role(payment)
        other_role = self.get_other_role(payment)
        logger.info(f"~~~~~~~~~~~~~~~~ready_for_settlement~~~~~~~~~~~{my_role}")

        # TODO: check validity of KYC data
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
                raise BusinessForceAbort("Transaction was not created")

            if (
                not get_transaction_status(transaction_id)
                == TransactionStatus.OFF_CHAIN_STARTED
            ):
                logger.info("@@@kyc in wrong state")
                raise BusinessForceAbort(
                    f"Transaction has wrong status {get_transaction_status(transaction_id)}"
                )

            update_transaction(
                transaction_id=transaction_id,
                status=TransactionStatus.READY_FOR_ON_CHAIN,
            )
        logger.info("@@@kyc ready to settle")
        return True
