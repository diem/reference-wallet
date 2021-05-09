from ..vasp_proxy import VaspProxy

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def test_get_info_charge(validator, vasp_proxy: VaspProxy):
    # Step 1: vasp_proxy create payment info
    reference_id, validator_address = validator.prepare_payment_info("charge")
    # get validator saved payment info
    validator_payment_info = validator.get_payment_info(reference_id, validator_address)
    assert validator_payment_info is not None

    # Step 2: trigger payment_info_command
    vasp_proxy_payment_info = vasp_proxy.get_payment_info(
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
        vasp_proxy_payment_info.expiration == validator_payment_info.expiration is None
    )


def test_get_info_auth(validator, vasp_proxy: VaspProxy):
    # Step 1: vasp_proxy create payment info
    reference_id, validator_address = validator.prepare_payment_info("auth")
    # get validator saved payment info
    validator_payment_info = validator.get_payment_info(reference_id, validator_address)
    assert validator_payment_info is not None

    # Step 2: trigger payment_info_command
    vasp_proxy_payment_info = vasp_proxy.get_payment_info(
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
