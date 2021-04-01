from flask.testing import Client
from flask import Response
import pytest
from wallet.storage import User
from datetime import datetime, timedelta
from wallet.services import user as users_service


@pytest.fixture
def mock_get_user_by_reset_token_valid_password_reset_token_expiration(monkeypatch):
    def mock(reset_token: str) -> User:
        return User(
            password_reset_token_expiration=datetime.now() + timedelta(minutes=5)
        )

    monkeypatch.setattr(users_service, "get_user_by_reset_token", mock)


@pytest.fixture
def mock_get_user_by_reset_token_invalid_password_reset_token_expiration(monkeypatch):
    def mock(reset_token: str) -> User:
        return User(
            password_reset_token_expiration=datetime.now() - timedelta(minutes=5)
        )

    monkeypatch.setattr(users_service, "get_user_by_reset_token", mock)


@pytest.fixture
def mock_get_user_by_reset_token_unknown_user(monkeypatch):
    def mock(reset_token: str) -> User:
        return None

    monkeypatch.setattr(users_service, "get_user_by_reset_token", mock)


@pytest.fixture
def mock_update_password(monkeypatch):
    def mock(user_id, new_password) -> User:
        return None

    monkeypatch.setattr(users_service, "update_password", mock)


class TestResetPassword:
    def test_for_unknown_user(
        self,
        authorized_client: Client,
        mock_get_user_by_reset_token_unknown_user,
    ):
        rv: Response = authorized_client.post(
            "/user/actions/reset_password",
            json={
                "token": "token",
                "new_password": "new_password",
            },
        )

        assert rv.status_code == 401, rv.data
        assert rv.get_json()["error"] == "Unknown user"

    def test_with_valid_password_reset_token_expiration(
        self,
        authorized_client: Client,
        mock_get_user_by_reset_token_valid_password_reset_token_expiration,
        mock_update_password,
    ):
        rv: Response = authorized_client.post(
            "/user/actions/reset_password",
            json={
                "token": "token",
                "new_password": "new_password",
            },
        )

        assert rv.status_code == 200, rv.data
        assert rv.get_json() is not None
        assert rv.get_json()["success"] == True

    def test_with_invalid_password_reset_token_expiration(
        self,
        authorized_client: Client,
        mock_get_user_by_reset_token_invalid_password_reset_token_expiration,
        mock_update_password,
    ):
        rv: Response = authorized_client.post(
            "/user/actions/reset_password",
            json={
                "token": "token",
                "new_password": "new_password",
            },
        )

        assert rv.status_code == 401, rv.data
        assert rv.get_json()["error"] == "Expired refresh token"
