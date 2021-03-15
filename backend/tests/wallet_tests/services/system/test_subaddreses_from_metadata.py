from diem import diem_types, txnmetadata as metadata

from wallet.services.system import subaddreses_from_metadata


def test_general_metadata():
    expected_r = bytes.fromhex("1122334455667788")
    expected_s = bytes.fromhex("1122334455667789")

    both_set_meta = metadata.general_metadata(expected_s, expected_r).hex()
    r, s = subaddreses_from_metadata(both_set_meta)
    assert r == expected_r.hex()
    assert s == expected_s.hex()

    both_empty_meta = metadata.general_metadata().hex()
    r, s = subaddreses_from_metadata(both_empty_meta)
    assert r is None
    assert s is None

    only_r_meta = metadata.general_metadata(to_subaddress=expected_r).hex()
    r, s = subaddreses_from_metadata(only_r_meta)
    assert r == expected_r.hex()
    assert s is None

    only_s_meta = metadata.general_metadata(from_subaddress=expected_s).hex()
    r, s = subaddreses_from_metadata(only_s_meta)
    assert r is None
    assert s == expected_s.hex()


def test_refund_metadata():
    meta = metadata.refund_metadata(
        original_transaction_version=1,
        reason=diem_types.RefundReason__InvalidSubaddress(),
    ).hex()
    r, s = subaddreses_from_metadata(meta)
    assert r is None
    assert s is None
