# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Tuple

from pylibra import LibraNetwork, AccountResource

from libra_utils.custody import Custody
from libra_utils.libra import (
    get_network_supported_currencies,
    mint_and_wait,
    wait_for_account_seq,
    create_account,
    gen_subaddr,
    TransactionMetadata,
    encode_subaddr,
    encode_txn_metadata,
)
from libra_utils.types.currencies import LibraCurrency

api = LibraNetwork()


class Vasp:
    def __init__(self, custody_account_name: str):
        self._custody: Custody = Custody()
        self._custody_account_name = custody_account_name
        self.vasp_address = self._custody.get_account_address(
            self._custody_account_name
        )
        self.vasp_auth_key = self._custody.get_account_auth_key(
            self._custody_account_name
        )

    def setup_blockchain(self):
        print("===Start VASP onchain account setup===")
        account = create_account(self.vasp_auth_key, self.vasp_address)
        print(f"===VASP account has been created successfully {account}===")

        for currency in get_network_supported_currencies():
            self._add_currency_to_vasp_account(LibraCurrency[currency.code])

    def _add_currency_to_vasp_account(
        self, currency: LibraCurrency, gas_currency: LibraCurrency = LibraCurrency.LBR,
    ) -> None:
        """Send a transaction on-chain for adding a new currency to account"""
        account = self._vasp_account()
        seq = account.sequence

        if currency.value in account.balances.keys():
            print(
                f"Currency {currency.value} is already supported by account {account} no need to add it."
            )
            return

        tx = self._custody.create_add_currency_to_vasp_transaction(
            account_name=self._custody_account_name,
            currency=currency,
            gas_currency=gas_currency,
        )

        api.sendTransaction(tx)
        wait_for_account_seq(self.vasp_address, seq + 1)

        print(
            f"Currency support for {currency.value} enabled in VASP account {account}"
        )

    def _vasp_account(self) -> AccountResource:
        return api.getAccount(self.vasp_address)

    def create_vasp_account(self):
        mint_and_wait(self.vasp_auth_key, 1_000_000, LibraCurrency.LBR)
        account = self._vasp_account()

        if not account:
            raise Exception(
                f"Could not create vasp account for auth key {self.vasp_auth_key}"
            )

        return account

    def send_transaction(
        self,
        currency: LibraCurrency,
        amount: int,
        dest_vasp_address: str,
        dest_sub_address: str,
        source_subaddr=None,
    ) -> Tuple[int, int]:
        seq = self._vasp_account().sequence

        if source_subaddr is None:
            source_subaddr = gen_subaddr()

        meta_obj = TransactionMetadata(
            to_subaddr=encode_subaddr(dest_sub_address),
            from_subaddr=encode_subaddr(source_subaddr),
        )

        meta = encode_txn_metadata(meta_obj)

        tx = self._custody.create_signed_p2p_transaction(
            account_name=self._custody_account_name,
            num_coins_microlibra=amount,
            currency=currency.value,
            receiver_addr=dest_vasp_address,
            metadata=meta,
        )

        api.sendTransaction(tx)

        wait_for_account_seq(self.vasp_address, seq + 1)

        tx, _ = api.transaction_by_acc_seq(addr_hex=self.vasp_address, seq=seq)

        if not tx:
            raise Exception(
                f"Transaction send from {self.vasp_address} to {dest_vasp_address} failed"
            )

        return tx.version, tx.sequence
