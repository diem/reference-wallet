from typing import Tuple, Optional

import context
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from diem import offchain, identifier
from wallet.services import kyc, account
from wallet.storage import models

PaymentCommandModel = models.PaymentCommand


def hrp() -> str:
    return context.get().config.diem_address_hrp()


def compliance_private_key() -> Ed25519PrivateKey:
    return context.get().config.compliance_private_key()


def offchain_client() -> offchain.Client:
    return context.get().offchain_client


def account_address_and_subaddress(account_id: str) -> Tuple[str, Optional[str]]:
    account_address, sub = identifier.decode_account(
        account_id, context.get().config.diem_address_hrp()
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
