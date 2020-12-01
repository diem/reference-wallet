# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import logging, time
from offchainapi.crypto import ComplianceKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from dataclasses import dataclass
from diem import (
    jsonrpc,
    utils,
    diem_types,
    stdlib,
    txnmetadata,
    LocalAccount,
    AuthKey,
)
from . import config, stubs

logger = logging.getLogger(__name__)


@dataclass
class Context:
    config: config.Config
    jsonrpc_client: jsonrpc.Client
    custody: stubs.custody.Client

    # ---- delegate to jsonrpc client start ----

    def get_vasp_base_url(self, address: str) -> str:
        account = self.jsonrpc_client.get_parent_vasp_account(address)
        base_url = account.role.base_url

        if not base_url:
            raise ValueError(f"base url is empty, peer vasp address: {address}")

        return base_url

    def get_vasp_public_compliance_key(self, address: str) -> ComplianceKey:
        account = self.jsonrpc_client.get_parent_vasp_account(address)
        key = account.role.compliance_key

        if not key:
            raise ValueError(
                f"compliance verification key is empty, peer vasp address: {address}"
            )

        ckey = ComplianceKey.from_pub_bytes(bytes.fromhex(key))
        logger.info(f"vasp ({address}) compliance public key: {ckey.export_pub()}")
        return ckey

    def reset_dual_attestation_info(self):
        txn = self.create_transaction(
            stdlib.encode_rotate_dual_attestation_info_script(
                self.config.base_url.encode("UTF-8"),
                self.config.compliance_public_key_bytes(),
            )
        )

        self._submit_and_wait(txn)

    def p2p_by_general(
        self,
        currency: str,
        amount: int,
        receiver_vasp_address: str,
        receiver_sub_address: str,
        sender_sub_address: str,
    ) -> jsonrpc.Transaction:
        metadata = txnmetadata.general_metadata(
            from_subaddress=bytes.fromhex(sender_sub_address),
            to_subaddress=bytes.fromhex(receiver_sub_address),
        )
        return self._p2p_transfer(
            currency, amount, receiver_vasp_address, metadata, b""
        )

    def p2p_by_travel_rule(
        self,
        currency: str,
        amount: int,
        receiver_vasp_address: str,
        off_chain_reference_id: str,
        metadata_signature: bytes,
    ) -> jsonrpc.Transaction:
        metadata, _ = txnmetadata.travel_rule(
            off_chain_reference_id, self.config.vasp_account_address(), amount,
        )
        return self._p2p_transfer(
            currency, amount, receiver_vasp_address, metadata, metadata_signature
        )

    def _p2p_transfer(
        self, currency, amount, receiver_vasp_address, metadata, signature
    ) -> jsonrpc.Transaction:
        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency),
            payee=utils.account_address(receiver_vasp_address),
            amount=diem_types.st.uint64(amount),
            metadata=metadata,
            metadata_signature=signature,
        )

        txn = self.create_transaction(script)
        return self._submit_and_wait(txn)

    def _submit_and_wait(
        self, txn: diem_types.SignedTransaction
    ) -> jsonrpc.Transaction:
        self.jsonrpc_client.submit(txn)
        return self.jsonrpc_client.wait_for_transaction(txn, 30)

    # ---- delegate to jsonrpc client end ----

    # ---- diem transaction utils start ----

    def create_transaction(
        self, script: diem_types.Script
    ) -> diem_types.SignedTransaction:
        address = self.config.vasp_account_address()
        seq = self.jsonrpc_client.get_account_sequence(address)
        txn = diem_types.RawTransaction(
            sender=address,
            sequence_number=diem_types.st.uint64(seq),
            payload=diem_types.TransactionPayload__Script(value=script),
            max_gas_amount=diem_types.st.uint64(1_000_000),
            gas_unit_price=diem_types.st.uint64(0),
            gas_currency_code=self.config.gas_currency_code,
            expiration_timestamp_secs=diem_types.st.uint64(int(time.time()) + 30),
            chain_id=diem_types.ChainId.from_int(self.config.chain_id),
        )
        sig = self.sign(utils.raw_transaction_signing_msg(txn))
        return utils.create_signed_transaction(txn, self.public_key_bytes(), sig)

    # ---- diem transaction utils end ----

    # ---- delegate to custody start ----

    def register_wallet_private_key(self, private_key: Ed25519PrivateKey) -> None:
        self.custody.register(self.config.wallet_custody_account_name, private_key)

    def sign(self, msg: bytes) -> bytes:
        return self.custody.sign(self.config.wallet_custody_account_name, msg)

    def public_key_bytes(self) -> bytes:
        return self.custody.get_public_key(self.config.wallet_custody_account_name)

    def auth_key(self) -> AuthKey:
        return AuthKey.from_public_key(
            Ed25519PublicKey.from_public_bytes(self.public_key_bytes())
        )

    # ---- delegate to custody end ----


def from_config(config: config.Config) -> Context:
    return Context(
        config=config,
        jsonrpc_client=jsonrpc.Client(config.json_rpc_url),
        custody=stubs.custody.from_env(),
    )


def from_env() -> Context:
    return from_config(config.from_env())


def for_local_dev() -> Context:
    return generate(1)


def generate(index: int) -> Context:
    account, conf = config.generate(index)
    ctx = from_config(conf)
    ctx.register_wallet_private_key(account.private_key)

    return ctx
