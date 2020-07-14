# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

# TODO: move these to a separate package
# # pyre-ignore-all-errors

# from pylibra import LibraNetwork
# from _pytest.monkeypatch import MonkeyPatch

# from dramatiq.brokers.stub import StubBroker
# from dramatiq.worker import Worker

# from tests.wallet_tests.pylibra_mocks import AccountMocker
# from webapp.dispatcher import transfer
# from wallet.storage import (
#     get_account_balance,
#     add_account_balance,
# )
# from wallet.types import LibraCurrency
# from ..conftest import FakeUsers
# from webapp.api import get_transaction_response_object
# from wallet.storage.libra_utils import (
#     get_user_transactions_for_currency,
#     get_new_subaddress,
#     encode_full_addr,
# )
# from wallet.custody import LRW_VASP_ADDRESS_STR


# def test_transfer_in_network(
#     monkeypatch: MonkeyPatch,
#     fake_db: None,
#     fake_users: FakeUsers,
#     stub_broker: StubBroker,
#     stub_worker: Worker,
# ) -> None:

#     sender = fake_users.get()
#     receiver = fake_users.get()
#     sender_id = sender.id
#     receiver_id = receiver.id
#     currency = LibraCurrency.Coin1
#     add_account_balance(sender_id, 10, currency)
#     receiver_address = encode_full_addr(
#         LRW_VASP_ADDRESS_STR, get_new_subaddress(receiver_id)
#     )
#     amount = 10
#     prev_sender_balance = get_account_balance(sender_id, currency)
#     prev_receiver_balance = get_account_balance(receiver_id, currency)

#     transfer(sender_id, receiver_address, amount, currency)

#     stub_broker.join("default")
#     stub_worker.join()

#     assert (prev_sender_balance - amount) == get_account_balance(sender_id, currency)
#     assert (prev_receiver_balance + amount) == get_account_balance(
#         receiver_id, currency
#     )


# def test_transfer_out_of_network(
#     monkeypatch: MonkeyPatch,
#     fake_db: None,
#     fake_users: FakeUsers,
#     stub_broker: StubBroker,
#     stub_worker: Worker,
# ) -> None:

#     account_mocker = AccountMocker()

#     monkeypatch.setattr(LibraNetwork, "getAccount", account_mocker.get_account)
#     monkeypatch.setattr(LibraNetwork, "sendTransaction", lambda *args: None)

#     fake_user1 = fake_users.get()

#     amount = 10
#     sender_id = fake_user1.id
#     receiver_vasp = b"B" * 16
#     receiver_subaddr = b"b" * 8
#     receiver_address = encode_full_addr(receiver_vasp.hex(), receiver_subaddr.hex())

#     currency = LibraCurrency.Coin1
#     add_account_balance(sender_id, amount, currency)
#     prev_account_balance = get_account_balance(sender_id, currency)
#     transfer(sender_id, receiver_address, amount, currency)
#     transactions = get_user_transactions_for_currency(sender_id, LibraCurrency.Coin1)
#     transaction_response_objects = [
#         get_transaction_response_object(fake_user1.id, tx) for tx in transactions
#     ]
#     assert transaction_response_objects[0]["amount"] == amount
#     assert transaction_response_objects[0]["currency"] == currency

#     stub_broker.join("default")
#     stub_worker.join()
#     assert (prev_account_balance - amount) == get_account_balance(sender_id, currency)
