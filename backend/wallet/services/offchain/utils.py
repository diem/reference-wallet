from typing import Tuple, Optional

import context
import typing
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import identifier, diem_types, serde_types, jsonrpc
from offchain.types import (
    GetInfoCommandResponse,
    InitChargePaymentResponse,
)
from wallet.services import kyc, account
from wallet.storage import get_account_id_from_subaddr
from diem import txnmetadata

import offchain
import logging

logger = logging.getLogger(__name__)

def hrp() -> str:
    return context.get().config.diem_address_hrp()


def compliance_private_key() -> Ed25519PrivateKey:
    return context.get().config.compliance_private_key()


def offchain_client() -> offchain.Client:
    return context.get().offchain_client


def account_address_and_subaddress(address: str) -> Tuple[str, Optional[str]]:
    account_address, sub = identifier.decode_account(
        address, context.get().config.diem_address_hrp()
    )
    return account_address.to_hex(), sub.hex() if sub else None


def user_kyc_data(user_id: int) -> offchain.KycDataObject:
    return offchain.types.from_dict(
        kyc.get_user_kyc_info(user_id), offchain.KycDataObject, ""
    )


def generate_my_address(account_id):
    vasp_address = context.get().config.vasp_address
    sub_address = account.generate_new_subaddress(account_id)
    return identifier.encode_account(vasp_address, sub_address, hrp())


def evaluate_kyc_data(command: offchain.PaymentCommand) -> offchain.PaymentCommand:
    # todo: evaluate command.opponent_actor_obj().kyc_data
    # when pass evaluation, we send kyc data as receiver or ready for settlement as sender
    if command.is_receiver():
        return _send_kyc_data_and_recipient_signature(command)
    return command.new_command(status=offchain.Status.ready_for_settlement)


def _send_kyc_data_and_recipient_signature(
    command: offchain.PaymentCommand,
) -> offchain.PaymentCommand:
    sig_msg = command.travel_rule_metadata_signature_message(hrp())
    user_id = get_account_id_from_subaddr(command.receiver_subaddress(hrp()).hex())

    return command.new_command(
        recipient_signature=compliance_private_key().sign(sig_msg).hex(),
        kyc_data=user_kyc_data(user_id),
        status=offchain.Status.ready_for_settlement,
    )


def jws_response(
    cid: Optional[str],
    result_object: typing.Optional[
        typing.Union[GetInfoCommandResponse, InitChargePaymentResponse]
    ] = None,
    err: Optional[offchain.OffChainErrorObject] = None,
):
    code = 400 if err else 200
    resp = offchain.reply_request(
        cid=cid,
        result_object=result_object,
        err=err,
    )
    return code, offchain.jws.serialize(resp, compliance_private_key().sign)


def get_p2m_metadata_by_ref_id(reference_id = "d74ace9c-cbd4-495b-9932-ad185e3f3301"):
   metadata = txnmetadata.payment_metadata(reference_id)
   return diem_types.Metadata__TravelRuleMetadata.bcs_deserialize(metadata)


def submit_p2m_txn() -> jsonrpc.Transaction:
    sender_bech32 = identifier.encode_account("68f626eb8d798f6b618a119d172a2559", None, 'tdm')
    sender_address = identifier.decode_account_address(sender_bech32, 'tdm')

    amount = 1000#2000000000  # there are 6 0's after the real amount. if the amount >= 1000$ then receipient_signature is needed. otherwise, use b'' for empty bytes array

    metadata = get_p2m_metadata_by_ref_id()

    attest = txnmetadata.Attest(metadata=metadata, sender_address=sender_address,
                                amount=serde_types.uint64(amount))  # pyre-ignore
    signing_msg = attest.bcs_serialize() + b"@@$$DIEM_ATTEST$$@@"

    reciever_bech32 = identifier.encode_account("17ab529b6d8afc6eb810b83d061eb7e7", None, 'tdm')
    reciever_address = identifier.decode_account_address(reciever_bech32, 'tdm')

    recipient_signature = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex("703fff5c70d55896d9ffcbdaa0e9821f83bd95317bd34bcce10e6507a67a0aa3")
    ).sign(signing_msg).hex()

    return context.get().p2p_by_travel_rule(
        reciever_address,
        "XUS",
        amount,
        metadata.bcs_serialize(),
        b'' #bytes.fromhex(recipient_signature), #b''
    )
