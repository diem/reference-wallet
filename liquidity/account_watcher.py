# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from argparse import ArgumentParser
from datetime import datetime
from time import time, sleep

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from diem import (
    testnet,
    jsonrpc,
    LocalAccount,
    stdlib,
    utils,
    AuthKey,
    txnmetadata,
    diem_types,
)

JSON_RPC_URL_DEFAULT = os.getenv("JSON_RPC_URL", testnet.JSON_RPC_URL)
CHAIN_ID_DEFAULT = int(os.getenv("CHAIN_ID", testnet.CHAIN_ID))

REFILL_DEFAULT = 100_000
THRESHOLD_DEFAULT = 10_000
CURRENCIES_DEFAULT = ["Coin1"]
SLEEP_DEFAULT = 10

run_with_env_vars = os.getenv("ACCOUNT_WATCHER_AUTH_KEY", default=False)

if run_with_env_vars:
    private_key = os.getenv("ACCOUNT_WATCHER_PRIVATE_KEY", default=None)
    auth_key = os.getenv("ACCOUNT_WATCHER_AUTH_KEY", default=None)
    refill_amount_human = os.getenv("ACCOUNT_WATCHER_AMOUNT", default=REFILL_DEFAULT)
    threshold_amount_human = os.getenv(
        "ACCOUNT_WATCHER_THRESHOLD", default=THRESHOLD_DEFAULT
    )
    currencies = os.getenv("ACCOUNT_WATCHER_CURRENCIES", default=CURRENCIES_DEFAULT)
    if currencies != CURRENCIES_DEFAULT:
        currencies = currencies.split(" ")
    network_chainid = int(os.getenv("ACCOUNT_WATCHER_CHAIN_ID", default=CHAIN_ID_DEFAULT))
    network_json_rpc_url = os.getenv(
        "ACCOUNT_WATCHER_JSON_RPC_URL", default=JSON_RPC_URL_DEFAULT
    )
    sleep_interval = os.getenv("ACCOUNT_WATCHER_SLEEP_INTERVAL", SLEEP_DEFAULT)
else:
    parser = ArgumentParser()
    parser.add_argument(
        "-pk",
        "--private-key",
        help="private key (hex) of the sender account (default to mint)",
        required=False,
    )
    parser.add_argument(
        "-ak",
        "--auth-key",
        help="auth key (hex) of the receiver account",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--threshold",
        help="minimum balance in any given currency to trigger refill",
        default=THRESHOLD_DEFAULT,
    )
    parser.add_argument(
        "-a",
        "--amount",
        help="amount to refill the account whenever needed",
        default=REFILL_DEFAULT,
    )
    parser.add_argument(
        "-c",
        "--currencies",
        help="currency list to watch",
        nargs="*",
        default=CURRENCIES_DEFAULT,
    )
    parser.add_argument(
        "-n",
        "--network-chainid",
        help="network chain id (defaults to TESTNET)",
        type=int,
        default=CHAIN_ID_DEFAULT,
    )
    parser.add_argument(
        "-j",
        "--network-json-rpc-url",
        help="network JSON-RPC URL (defaults to TESTNET)",
        type=int,
        default=JSON_RPC_URL_DEFAULT,
    )
    parser.add_argument(
        "-s",
        "--sleep-interval",
        help="sleep interval (in seconds) between each round of account check",
        default=SLEEP_DEFAULT,
    )

    args = parser.parse_args()
    private_key = args.private_key
    auth_key = args.auth_key
    refill_amount_human = args.amount
    threshold_amount_human = args.threshold
    currencies = args.currencies
    network_chainid = args.network_chainid
    network_json_rpc_url = args.network_json_rpc_url
    sleep_interval = args.sleep_interval

if auth_key is None:
    print("Must get an authentication key to watch!")
    sys.exit(1)

diem_client = jsonrpc.Client(network_json_rpc_url)

watched_account_auth_key = AuthKey(bytes.fromhex(auth_key))
watched_account_addr = watched_account_auth_key.account_address()
watched_account_addr_hex = utils.account_address_hex(watched_account_addr)

refill_amount = int(refill_amount_human) * 1_000_000  # to microdiem
threshold_amount = int(threshold_amount_human) * 1_000_000  # to microdiem
sleep_interval = float(sleep_interval)

while True:
    print(f'current datetime: {datetime.now().isoformat().replace("T", " ")}')

    for currency in currencies:
        currency_balance = next(
            b.amount for b in diem_client.get_account(watched_account_addr).balances
        )
        print(f"{currency} balance is {currency_balance} ",)

        if currency_balance > threshold_amount:
            print(f"which is enough!")
        else:
            print(f"need to refill...")

            if network_chainid == testnet.CHAIN_ID.value and private_key is None:
                print(
                    f"running in TESTNET, using faucet to mint {refill_amount} {currency}... ",
                )
                faucet = testnet.Faucet(diem_client)
                faucet.mint(auth_key, refill_amount, currency)
            else:
                # use DD private key to send P2P transaction to the watched account
                sender_account = LocalAccount(
                    Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key))
                )
                sender_account_info = diem_client.get_account(
                    sender_account.account_address
                )
                sender_account_addr_hex = utils.account_address_hex(
                    sender_account.account_address
                )

                script = stdlib.encode_peer_to_peer_with_metadata_script(
                    currency=utils.currency_code(currency),
                    payee=watched_account_addr,
                    amount=refill_amount,
                    metadata=txnmetadata.general_metadata(
                        from_subaddress=utils.account_address_bytes(
                            sender_account.account_address
                        ),
                        to_subaddress=utils.account_address_bytes(watched_account_addr),
                    ),
                    metadata_signature=b"",
                )
                raw_tx = diem_types.RawTransaction(
                    sender=sender_account.account_address,
                    sequence_number=sender_account_info.sequence_number,
                    payload=diem_types.TransactionPayload__Script(script),
                    max_gas_amount=1_000_000,
                    gas_unit_price=0,
                    gas_currency_code=currency,
                    expiration_timestamp_secs=int(time()) + 30,
                    chain_id=diem_types.ChainId.from_int(network_chainid),
                )
                tx = sender_account.sign(raw_tx)

                print(
                    f"sending transaction from account {sender_account_addr_hex} "
                    f"(seq {sender_account_info.sequence_number}) "
                    f"to {watched_account_addr_hex}",
                )
                diem_client.submit(tx)
                diem_client.wait_for_transaction(tx, 30)
                print("done!")

    print(f"sleeping for {sleep_interval}")
    sleep(sleep_interval)
