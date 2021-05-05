from ..vasp_proxy import VaspProxy

ONE_YEAR_SECONDS = 356 * 24 * 60 * 60


def test_get_info(validator, vasp_proxy: VaspProxy):
    # Step 1: vasp_proxy create payment info
    reference_id, validator_address = validator.prepare_payment_info()

    # Step 2: trigger payment_info_command
    payment_info = vasp_proxy.get_payment_info(reference_id, validator_address)

    assert payment_info is not None
