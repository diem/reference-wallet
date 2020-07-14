# pyre-ignore-all-errors

# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple, List

from bech32 import encode, decode
from pylibra import LibraNetwork, CurrencyInfo, AccountResource, FaucetUtils

ASSOC_ADDRESS: str = "0000000000000000000000000a550c18"
ASSOC_AUTHKEY: str = "3126dc954143b1282565e8829cd8cdfdc179db444f64b406dee28015fce7f392"

VASP_ADDRESS_LENGTH: int = 16
SUBADDRESS_LENGTH: int = 8

api = LibraNetwork()


# tlb for testnet, lbr for mainnet
def encode_full_addr(
    vasp_addr: str, subaddr: Optional[str] = None, hrp: str = "tlb",
) -> str:
    if subaddr is None or subaddr == "":
        version = 0
        raw_bytes = bytes.fromhex(vasp_addr)
    else:
        version = 1
        raw_bytes_subaddr = encode_subaddr(subaddr)
        raw_bytes = bytes.fromhex(vasp_addr) + raw_bytes_subaddr
    encoded_addr = encode(hrp, version, raw_bytes)
    if encoded_addr is None:
        raise ValueError(f'Cannot convert to LibraAddress: "{raw_bytes}"')

    return encoded_addr


# returns address, subaddress tuple
def decode_full_addr(
    encoded_address: str, hrp: str = "tlb"
) -> Tuple[str, Optional[str]]:
    assert hrp in ("lbr", "tlb")
    # Do basic bech32 decoding
    version, decoded_address = decode(hrp, encoded_address)
    if decoded_address is None:
        raise ValueError(f'Incorrect version or bech32 encoding: "{encoded_address}"')
    # Set the version
    if version == 0:
        # This is a libra network address without subaddress.
        if len(decoded_address) != VASP_ADDRESS_LENGTH:
            raise ValueError(
                f"Libra network address must be 16"
                f' bytes, found: "{len(decoded_address)}"'
            )
        return bytes(decoded_address).hex(), None

    elif version == 1:
        # This is a libra network sub-address
        if len(decoded_address) < VASP_ADDRESS_LENGTH + SUBADDRESS_LENGTH:
            raise ValueError(
                f"Libra network sub-address must be > 16+8"
                f' bytes, found: "{len(decoded_address)}"'
            )

        addr_bytes = bytes(decoded_address)
        return (
            addr_bytes[:VASP_ADDRESS_LENGTH].hex(),
            addr_bytes[VASP_ADDRESS_LENGTH:].hex(),
        )


def gen_raw_subaddr() -> bytes:
    """
    Return a raw subaddress bytestring of a given length
    """
    return os.urandom(SUBADDRESS_LENGTH)


def gen_subaddr() -> str:
    return decode_subaddr(gen_raw_subaddr())


def encode_subaddr(subaddr: str) -> bytes:
    return bytes.fromhex(subaddr)


def decode_subaddr(subaddr: bytes) -> str:
    return subaddr.hex()


@dataclass
class TransactionMetadata:
    def __init__(
        self,
        to_subaddr: bytes = b"",
        from_subaddr: bytes = b"",
        referenced_event: bytes = b"",
    ) -> None:
        self.to_subaddress: bytes = to_subaddr
        self.from_subaddress: bytes = from_subaddr
        self.referenced_event: bytes = referenced_event

    def to_bytes(self) -> bytes:
        ret = b""
        if self.to_subaddress:
            ret += b"\x01" + self.to_subaddress
        else:
            ret += b"\x00"

        if self.from_subaddress:
            ret += b"\x01" + self.from_subaddress
        else:
            ret += b"\x00"

        if self.referenced_event:
            ret += b"\x01" + self.referenced_event
        else:
            ret += b"\x00"

        return ret

    @staticmethod
    def from_bytes(lcs_bytes: bytes) -> "TransactionMetadata":
        """
        Parse transaction metadata by LCS standard. On error, return empty
        """
        if len(lcs_bytes) == 0:
            print("Metadata empty")
            return TransactionMetadata()

        curr_byte = 0
        to_subaddress, from_subaddress, referenced_event = b"", b"", b""

        try:
            to_subaddr_present = lcs_bytes[0] == 0x01
            curr_byte += 1
            if not to_subaddr_present:  # to_subaddress is mandatory
                return TransactionMetadata()
            to_subaddress = lcs_bytes[curr_byte : curr_byte + 8]
            curr_byte += 8

            from_subaddress_present = lcs_bytes[curr_byte] == 0x01
            curr_byte += 1
            if from_subaddress_present:
                from_subaddress = lcs_bytes[curr_byte : curr_byte + 8]
                curr_byte += 8

            referenced_event_present = lcs_bytes[curr_byte] == 0x01
            curr_byte += 1
            if referenced_event_present:
                referenced_event = lcs_bytes[curr_byte:]

            return TransactionMetadata(to_subaddress, from_subaddress, referenced_event)
        except IndexError:
            print("Metadata malformed")
            return TransactionMetadata()


def encode_txn_metadata(meta: TransactionMetadata) -> bytes:
    return meta.to_bytes()


def decode_txn_metadata(meta_bytes: bytes) -> "TransactionMetadata":
    return TransactionMetadata.from_bytes(meta_bytes)


def get_network_supported_currencies() -> List[CurrencyInfo]:
    api = LibraNetwork()
    return api.get_currencies()


def wait_for_account_seq(addr_hex: str, seq: int) -> AccountResource:
    num_tries = 0

    while num_tries < 1000:
        ar = api.getAccount(addr_hex)
        if ar is not None and ar.sequence >= seq:
            return ar
        time.sleep(1)
        num_tries += 1
    raise Exception("Wait for account sequence timed out!")


def mint_and_wait(authkey_hex: str, amount: int, currency: str) -> AccountResource:
    f = FaucetUtils()
    seq = f.mint(authkey_hex=authkey_hex, amount=amount, identifier=currency)
    return wait_for_account_seq(ASSOC_ADDRESS, seq)


def create_account(auth_key, public_address):
    """
    Create account with all supported blockchain currencies
    """
    account = api.getAccount(public_address)
    if not account:
        mint_and_wait(auth_key, 1_000_000, "LBR")
        account = api.getAccount(public_address)

        if not account:
            raise Exception(f"Could not create vasp account for auth key {auth_key}")

    return account
