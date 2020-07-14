# Copyright (c) The Libra Core Contributors
# SPDX-License-Identifier: Apache-2.0

from datetime import date
from typing import Optional

from wallet import services
from wallet.services import user as user_service, account as account_service
from wallet.storage import get_user, User
from wallet.types import RegistrationStatus


def is_verified(user_id: int) -> bool:
    user = get_user(user_id)
    return _is_verified(user)


def process_user_kyc(
    user_id,
    selected_fiat_currency: str,
    selected_language: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    dob: Optional[date] = None,
    phone: Optional[str] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    address_1: Optional[str] = None,
    address_2: Optional[str] = None,
    zip: Optional[str] = None,
):
    user_obj = dict(
        registration_status=RegistrationStatus.Pending,
        selected_fiat_currency=selected_fiat_currency,
        selected_language=selected_language,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone=phone,
        country=country,
        state=state,
        city=city,
        address_1=address_1,
        address_2=address_2,
        zip=zip,
    )
    user_service.update_user(user_id, **user_obj)

    if services.run_bg_tasks():
        from wallet.background_tasks.background import async_start_kyc

        async_start_kyc.send(user_id)
    else:
        verify_kyc(user_id=user_id)


def verify_kyc(user_id: int) -> None:
    user = get_user(user_id)
    if _is_verified(user):
        user_service.update_user(
            user_id=user_id, registration_status=RegistrationStatus.Approved
        )

    if user.first_name == "doctor" and user.last_name == "evil":
        user_service.update_user(
            user_id=user_id, registration_status=RegistrationStatus.Rejected
        )
    else:
        user_service.update_user(
            user_id=user_id, registration_status=RegistrationStatus.Approved
        )
        account_service.create_account(
            account_name=f"{user.username}-account", user_id=user.id
        )


def _is_verified(user: User) -> bool:
    return user.registration_status == RegistrationStatus.Approved
