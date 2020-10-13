# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from libra.testnet import Faucet
from libra.jsonrpc import Client
from libra import utils
from tests.wallet_tests.libra_client_sdk_mocks import (
    FaucetUtilsMock,
    LibraNetworkMock,
    TransactionsMocker,
)


def setup_mocks(vasp_addr):
    Faucet.mint = FaucetUtilsMock.mint
    Client.get_account = LibraNetworkMock.get_account
    Client.get_account_transaction = LibraNetworkMock.transaction_by_acc_seq
    Client.get_transactions = LibraNetworkMock.transactions_by_range
    Client.submit = LibraNetworkMock.sendTransaction

    TransactionsMocker.VASP_ADDR = vasp_addr
    utils.create_signed_transaction = TransactionsMocker.create_signed_p2p_transaction
