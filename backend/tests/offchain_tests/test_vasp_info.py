from libra import LocalAccount, testnet, libra_types, stdlib, utils
from offchainapi.crypto import ComplianceKey
from offchainapi.libra_address import LibraAddress
from cryptography.hazmat.primitives import serialization
from time import time
from offchain import LRWSimpleVASPInfo
import os


def test_vasp_info():
    # Setup peer account locally
    peer_account = LocalAccount.generate()
    peer_base_url = "https://testing_base_url.com"
    peer_compliance_key = ComplianceKey.generate().export_full()
    peer_compliance_public_key_bytes = (
        ComplianceKey.from_str(peer_compliance_key)
        .get_public()
        .public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
    )
    peer_compliance_public_key = ComplianceKey.from_pub_bytes(
        peer_compliance_public_key_bytes
    )
    libra_client = testnet.create_client()

    # Setup peer account onchain
    faucet = testnet.Faucet(libra_client)
    faucet.mint(peer_account.auth_key.hex(), 1_000_000, "Coin1")

    account_info = libra_client.get_account(peer_account.account_address)
    if not account_info:
        raise RuntimeError(f"Could not find account {peer_account.account_address}")

    script = stdlib.encode_rotate_dual_attestation_info_script(
        peer_base_url.encode("UTF-8"), peer_compliance_public_key_bytes
    )

    raw_tx = libra_types.RawTransaction(
        sender=peer_account.account_address,
        sequence_number=account_info.sequence_number,
        payload=libra_types.TransactionPayload__Script(script),
        max_gas_amount=1_000_000,
        gas_unit_price=0,
        gas_currency_code="Coin1",
        expiration_timestamp_secs=int(time()) + 30,
        chain_id=testnet.CHAIN_ID,
    )
    tx = peer_account.sign(raw_tx)

    libra_client.submit(tx)
    libra_client.wait_for_transaction(tx)

    vasp_info = LRWSimpleVASPInfo(LibraAddress.from_hex(os.getenv("VASP_ADDR")))
    peer_libra_address = LibraAddress.from_hex(
        onchain_address_hex=utils.account_address_hex(peer_account.account_address),
        hrp="tlb",
    )

    # Testing VASP info intefaces
    assert vasp_info.get_peer_base_url(peer_libra_address) == peer_base_url
    assert (
        vasp_info.get_peer_compliance_verification_key(peer_libra_address.as_str())
        == peer_compliance_public_key
    )
    assert vasp_info.get_my_compliance_signature_key(
        LibraAddress.from_hex(os.getenv("VASP_ADDR"))
    ) == ComplianceKey.from_str(os.getenv("VASP_COMPLIANCE_KEY"))
