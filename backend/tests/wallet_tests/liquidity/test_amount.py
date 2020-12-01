# pyre-ignore-all-errors

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem_utils.precise_amount import Amount

ONE_DIEM = Amount().deserialize(1000000)
TWO_DIEM = Amount().deserialize(2000000)
TENTH_MILLIDIEM = Amount().deserialize(100)
MAX_PRECISION_DIEM = Amount().deserialize(10000000000000000009)


class TestAmount:
    def test_mul(self):
        x: Amount = ONE_DIEM * ONE_DIEM
        assert str(x) == "1.000000"
        assert x.serialize() == 1000000

        x: Amount = TENTH_MILLIDIEM * TWO_DIEM
        assert str(x) == "0.000200"
        assert x.serialize() == 200

        x: Amount = MAX_PRECISION_DIEM * TWO_DIEM
        assert str(x) == "20000000000000.000018"
        assert x.serialize() == 20000000000000000018

    def test_div(self):
        x: Amount = ONE_DIEM / ONE_DIEM
        assert str(x) == "1.000000"
        assert x.serialize() == 1000000

        x: Amount = ONE_DIEM / TWO_DIEM
        assert str(x) == "0.500000"
        assert x.serialize() == 500000

        x: Amount = MAX_PRECISION_DIEM / TWO_DIEM
        assert str(x) == "5000000000000.000004"
        assert x.serialize() == 5000000000000000004
