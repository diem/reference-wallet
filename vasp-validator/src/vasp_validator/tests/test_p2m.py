from ..vasp_proxy import VaspProxy

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def test_charge_payment_flow(validator, vasp_proxy: VaspProxy):
    # Step 1: validator create payment info as receiver
    reference_id, validator_address = validator.prepare_payment_as_receiver("charge")
    # verify validator saved payment info
    validator_payment_info = validator.get_payment_details(
        reference_id, validator_address
    )
    assert validator_payment_info is not None

    # Step 2: vasp_proxy trigger payment_info_command execution
    vasp_proxy_payment_info = vasp_proxy.get_payment_details(
        reference_id, validator_address
    )
    # validate payment was created in vasp_proxy and the payment info equal to the payment info the validator hold
    assert vasp_proxy_payment_info is not None
    assert (
        vasp_proxy_payment_info.vasp_address
        == validator_payment_info.vasp_address
        == validator_address
    )
    assert (
        vasp_proxy_payment_info.reference_id
        == validator_payment_info.reference_id
        == reference_id
    )
    assert vasp_proxy_payment_info.merchant_name == validator_payment_info.merchant_name
    assert vasp_proxy_payment_info.action == validator_payment_info.action
    assert vasp_proxy_payment_info.currency == validator_payment_info.currency
    assert vasp_proxy_payment_info.amount == validator_payment_info.amount
    assert (
        vasp_proxy_payment_info.expiration == validator_payment_info.expiration is None
    )

    # 3. vasp_proxy approve the returned payment info
    vasp_proxy.approve_payment(reference_id, True)


def test_auth_payment_flow(validator, vasp_proxy: VaspProxy):
    # Step 1: vasp_proxy create payment info
    reference_id, validator_address = validator.prepare_payment_as_receiver("auth")
    # get validator saved payment info
    validator_payment_info = validator.get_payment_details(
        reference_id, validator_address
    )
    assert validator_payment_info is not None

    # Step 2: trigger payment_info_command
    vasp_proxy_payment_info = vasp_proxy.get_payment_details(
        reference_id, validator_address
    )

    assert vasp_proxy_payment_info is not None
    assert (
        vasp_proxy_payment_info.vasp_address
        == validator_payment_info.vasp_address
        == validator_address
    )
    assert (
        vasp_proxy_payment_info.reference_id
        == validator_payment_info.reference_id
        == reference_id
    )
    assert vasp_proxy_payment_info.merchant_name == validator_payment_info.merchant_name
    assert vasp_proxy_payment_info.action == validator_payment_info.action
    assert vasp_proxy_payment_info.currency == validator_payment_info.currency
    assert vasp_proxy_payment_info.amount == validator_payment_info.amount
    assert (
        vasp_proxy_payment_info.expiration
        == validator_payment_info.expiration
        is not None
    )
