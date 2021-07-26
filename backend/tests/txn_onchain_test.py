from diem import txnmetadata, identifier, diem_types, serde_types
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import context
import logging
from offchain import PaymentCommand

def test_p2p():
    sender_bech32 = identifier.encode_account("68f626eb8d798f6b618a119d172a2559", None, 'tdm')
    sender_address = identifier.decode_account_address(sender_bech32, 'tdm')

    amount = 2000000000

    metadata, signing_msg = method_name(sender_address, amount)

    reciever_bech32 = identifier.encode_account("17ab529b6d8afc6eb810b83d061eb7e7", None, 'tdm')
    reciever_address = identifier.decode_account_address(reciever_bech32, 'tdm')

    recipient_signature = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex("703fff5c70d55896d9ffcbdaa0e9821f83bd95317bd34bcce10e6507a67a0aa3")
    ).sign(signing_msg).hex()

    rpc_txn = context.get().p2p_by_travel_rule(
        reciever_address,
        "XUS",
        amount,
        metadata,
        bytes.fromhex(recipient_signature),
    )


def test_p2m():
    sender_bech32 = identifier.encode_account("68f626eb8d798f6b618a119d172a2559", None, 'tdm')
    sender_address = identifier.decode_account_address(sender_bech32, 'tdm')

    amount = 2000000000

    metadata = method_name_2()

    attest = txnmetadata.Attest(metadata=metadata, sender_address=sender_address, amount=serde_types.uint64(amount))  # pyre-ignore
    signing_msg = attest.bcs_serialize() + b"@@$$DIEM_ATTEST$$@@"

    reciever_bech32 = identifier.encode_account("17ab529b6d8afc6eb810b83d061eb7e7", None, 'tdm')
    reciever_address = identifier.decode_account_address(reciever_bech32, 'tdm')

    recipient_signature = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex("703fff5c70d55896d9ffcbdaa0e9821f83bd95317bd34bcce10e6507a67a0aa3")
    ).sign(signing_msg).hex()

    rpc_txn = context.get().p2p_by_travel_rule(
        reciever_address,
        "XUS",
        amount,
        metadata.bcs_serialize(),
        bytes.fromhex(recipient_signature),
    )


def method_name(sender_address, amount):
    return txnmetadata.travel_rule(
        "d74ace9c-cbd4-495b-9932-ad185e3f3301",
        sender_address,
        amount,
    )


def method_name_2(reference_id = "d74ace9c-cbd4-495b-9932-ad185e3f3301"):
   metadata = txnmetadata.payment_metadata(reference_id)
   return diem_types.Metadata__TravelRuleMetadata.bcs_deserialize(metadata)
