from wallet import storage
from wallet.types import RegistrationStatus
from tests.wallet_tests.resources.seeds.one_user_seeder import OneUser
from wallet.storage import db_session
from diem_utils.types.currencies import DiemCurrency
from datetime import datetime


def test_update_user_password_reset_token_expiration():
    user = OneUser.run(
        db_session, account_amount=100_000_000_000, account_currency=DiemCurrency.XUS
    )
    now = datetime.now()
    updated_user = storage.update_user(
        user_id=user.id, password_reset_token_expiration=now
    )
    assert updated_user.password_reset_token_expiration == now


def test_create_user() -> None:
    username = "fake_username"
    password_hash = "fake_hash"
    salt = "fake_salt"
    user_id = storage.add_user(
        username=username,
        password_hash=password_hash,
        salt=salt,
        registration_status=RegistrationStatus.Pending,
    )

    storage_user = storage.get_user(username=username)
    assert storage_user
    assert storage_user.id == user_id
