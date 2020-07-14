# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from pylibra import (
    FaucetUtils,
    LibraNetwork,
    TransactionUtils,
)

from libra_utils import custody
from tests.wallet_tests.pylibra_mocks import (
    FaucetUtilsMock,
    LibraNetworkMock,
    TransactionsMocker,
)


def setup_mocks(vasp_addr):
    FaucetUtils.mint = FaucetUtilsMock.mint
    LibraNetwork.getAccount = LibraNetworkMock.get_account
    LibraNetwork.transaction_by_acc_seq = LibraNetworkMock.transaction_by_acc_seq
    LibraNetwork.transactions_by_range = LibraNetworkMock.transactions_by_range
    LibraNetwork.sendTransaction = LibraNetworkMock.sendTransaction

    TransactionsMocker.VASP_ADDR = vasp_addr
    TransactionUtils.createSignedP2PTransaction = (
        TransactionsMocker.create_signed_p2p_transaction
    )
