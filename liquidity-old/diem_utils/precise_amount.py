# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from decimal import Decimal, Context, ROUND_HALF_EVEN
from typing import Optional


class _Amount:
    def __init__(self, fraction_digits: int, precision: int):
        self._fraction_digits = fraction_digits
        self._precision = precision
        self._quantizer = Decimal(1).scaleb(-fraction_digits)

        self._ctx = Context(prec=precision, rounding=ROUND_HALF_EVEN)
        self._value: Optional[Decimal] = None

    def deserialize(self, serialized_value):
        self._value = (
            self._ctx.create_decimal(serialized_value)
            .scaleb(-self._fraction_digits)
            .quantize(self._quantizer)
        )
        return self

    def serialize(self) -> int:
        return int(self._value.scaleb(self._fraction_digits))

    def set(self, value: Decimal):
        self._value = self._ctx.create_decimal(value).quantize(self._quantizer)
        return self

    def clone(self):
        raise NotImplementedError

    def __str__(self):
        return str(self._value)

    def __imul__(self, other):
        operand = other._value if isinstance(other, Amount) else other
        value = self._ctx.multiply(self._value, operand)
        return self.set(value)

    def __itruediv__(self, other):
        operand = other._value if isinstance(other, Amount) else other
        value = self._ctx.divide(self._value, operand)
        return self.set(value)

    def __mul__(self, other):
        return self.clone().__imul__(other)

    def __truediv__(self, other):
        return self.clone().__itruediv__(other)


class Amount(_Amount):
    FRACTION_DIGITS = 6
    PRECISION = 20
    unit = 1000000

    def __init__(self):
        super().__init__(
            fraction_digits=Amount.FRACTION_DIGITS, precision=Amount.PRECISION
        )

    def clone(self):
        return Amount().set(self._value)
