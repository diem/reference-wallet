import uuid

import context
from diem_utils.types.currencies import DiemCurrency
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.services.offchain import payment_command as pc_service
from wallet.storage import db_session


def test_add_payment_command(monkeypatch):
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )

    reference_id = str(uuid.uuid4())
    vasp_address = "tdm1pu2unysetgf3znj76juu532rmgrkf3wg8gqqx5qqs39vnj"
    merchant_name = "Bond & Gurki Pet Store"
    action = "charge"
    amount = 1000
    expiration = 1802010490
    pc_service.add_payment_command(
        account_id=user.account_id,
        reference_id=reference_id,
        vasp_address=vasp_address,
        merchant_name=merchant_name,
        action=action,
        currency=DiemCurrency.XUS,
        amount=amount,
        expiration=expiration,
    )

    payment_command = pc_service.get_payment_command(reference_id)

    assert payment_command
    assert payment_command.reference_id() == reference_id
    assert payment_command.opponent_address() == vasp_address
    assert payment_command.my_actor_address == context.get().config.vasp_address
    assert payment_command.payment.action.action == action
    assert payment_command.payment.action.amount == amount
    assert payment_command.payment.action.currency == DiemCurrency.XUS
