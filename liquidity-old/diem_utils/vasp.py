# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0
import secrets
from typing import Optional, Tuple

from diem import testnet, utils, stdlib, identifier, txnmetadata
from diem.jsonrpc import Client as DiemClient

from diem_utils.custody import Custody, _DEFAULT_ACCOUNT_NAME
from diem_utils.types.currencies import DiemCurrency


class VASPInfoNotFoundException(Exception):
    pass


class BaseURLNotFoundException(Exception):
    pass


class ComplianceKeyNotFoundException(Exception):
    pass


class Vasp:
    def __init__(
        self,
        diem_client: DiemClient,
        custody_account_name: Optional[str] = _DEFAULT_ACCOUNT_NAME,
    ):
        self._diem_client = diem_client
        self._custody: Custody = Custody()
        self._custody_account_name = custody_account_name

        self.account = self._custody.get_account(custody_account_name)
        self.address_str = utils.account_address_hex(self.account.account_address)

    def setup_blockchain(self, new_url: str, new_key: bytes):
        print("===Start VASP onchain account setup===")
        self.create_vasp_account()
        print(f"===VASP account has been created successfully===")

        for currency in self._diem_client.get_currencies():
            if currency.code == "Coin1":
                print(f"Adding {currency.code} to account {self.address_str}")
                self._add_currency_to_vasp_account(DiemCurrency[currency.code])

        self.rotate_dual_attestation_info(new_url, new_key)
        print(f"VASP dual attestation rotated: {new_url} {new_key.hex()}")

    def _add_currency_to_vasp_account(
        self,
        currency: DiemCurrency,
        gas_currency: DiemCurrency = DiemCurrency.Coin1,
    ) -> None:
        """Send a transaction on-chain for adding a new currency to account"""

        account_info = self.fetch_account_info()
        if not account_info:
            raise RuntimeError(f"Could not find account {self.address_str}")

        if currency.value in [b.currency for b in account_info.balances]:
            print(
                f"{currency.value} is already supported by account {self.address_str}"
            )
            return

        script = stdlib.encode_add_currency_to_account_script(
            utils.currency_code(currency.value)
        )

        tx = self._custody.create_transaction(
            self._custody_account_name,
            account_info.sequence_number,
            script,
            gas_currency,
        )
        self._diem_client.submit(tx)
        self._diem_client.wait_for_transaction(tx, 30)

        print(
            f"Currency support for {currency.value} enabled in VASP account {self.address_str}"
        )

    def create_vasp_account(self):
        faucet = testnet.Faucet(self._diem_client)
        faucet.mint(self.account.auth_key.hex(), 1_000_000, "Coin1")

    def fetch_account_info(self):
        return self._diem_client.get_account(self.account.account_address)

    def send_transaction(
        self,
        currency: DiemCurrency,
        amount: int,
        dest_vasp_address: str,
        dest_sub_address: str,
        source_sub_address: str = None,
    ) -> Tuple[int, int]:
        account_info = self.fetch_account_info()
        if not account_info:
            raise RuntimeError(f"Could not find account {self.address_str}")

        if source_sub_address is None:
            source_sub_address = secrets.token_hex(identifier.DIEM_SUBADDRESS_SIZE)

        meta = txnmetadata.general_metadata(
            from_subaddress=bytes.fromhex(source_sub_address),
            to_subaddress=bytes.fromhex(dest_sub_address),
        )

        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency.value),
            payee=utils.account_address(dest_vasp_address),
            amount=amount,
            metadata=meta,
            metadata_signature=b"",
        )

        tx = self._custody.create_transaction(
            self._custody_account_name,
            account_info.sequence_number,
            script,
            currency.value,
        )
        self._diem_client.submit(tx)

        onchain_tx = self._diem_client.wait_for_transaction(tx, 30)
        return onchain_tx.version, account_info.sequence_number

    def send_transaction_travel_rule(
        self,
        currency: DiemCurrency,
        amount: int,
        source_sub_address: str,
        dest_vasp_address: str,
        dest_sub_address: str,
        off_chain_reference_id: str,
        metadata_signature: bytes,
    ) -> Tuple[int, int]:
        account_info = self.fetch_account_info()
        if not account_info:
            raise RuntimeError(f"Could not find account {self.address_str}")

        sender = utils.account_address(self.address_str)
        metadata, metadata_sig = txnmetadata.travel_rule(
            off_chain_reference_id, sender, amount
        )

        # sender constructs transaction after off chain communication
        script = stdlib.encode_peer_to_peer_with_metadata_script(
            currency=utils.currency_code(currency.value),
            payee=utils.account_address(dest_vasp_address),
            amount=amount,
            metadata=metadata,
            metadata_signature=metadata_signature,
        )

        tx = self._custody.create_transaction(
            self._custody_account_name,
            account_info.sequence_number,
            script,
            currency.value,
        )
        self._diem_client.submit(tx)

        onchain_tx = self._diem_client.wait_for_transaction(tx, 30)
        return onchain_tx.version, account_info.sequence_number

    def rotate_dual_attestation_info(
        self,
        new_url: str,
        new_key: bytes,
        gas_currency: DiemCurrency = DiemCurrency.Coin1,
    ) -> None:
        """Send a transaction on-chain for rotating base url and compliance key"""

        account_info = self.fetch_account_info()
        if not account_info:
            raise RuntimeError(f"Could not find account {self.address_str}")

        script = stdlib.encode_rotate_dual_attestation_info_script(
            new_url.encode("UTF-8"), new_key
        )

        tx = self._custody.create_transaction(
            self._custody_account_name,
            account_info.sequence_number,
            script,
            gas_currency,
        )
        self._diem_client.submit(tx)
        self._diem_client.wait_for_transaction(tx, 30)
