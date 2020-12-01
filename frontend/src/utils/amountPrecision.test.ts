// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import {
  fiatFromHumanFriendly,
  fiatToDiemHumanFriendly,
  fiatToHumanFriendlyRate,
  diemAmountFromHumanFriendly,
  diemAmountToHumanFriendly,
} from "./amount-precision";

describe("Diem visual to internal conversions", () => {
  it("should be integer", () => {
    const converted = diemAmountFromHumanFriendly("1234.1234");
    expect(Number.isInteger(converted));
  });
  it("should be properly scaled", () => {
    const converted = diemAmountFromHumanFriendly("123456.123456");
    expect(converted).toBe(123456123456);
  });
  it("should be properly scaled even if not a fraction", () => {
    const converted = diemAmountFromHumanFriendly("1234");
    expect(converted).toBe(1234000000);
  });
  it("should be rounded if too many decimal digits", () => {
    const converted = diemAmountFromHumanFriendly("123456.123456789");
    expect(converted).toBe(123456123457);
  });
});

describe("Diem internal to visual conversions", () => {
  it("should be a decimal fraction", () => {
    const converted = diemAmountToHumanFriendly(123456123456);
    expect(converted).toBe("123456.123456");
  });
  it("should properly convert integer numbers", () => {
    const converted = diemAmountToHumanFriendly(123456000000);
    expect(converted).toBe("123456");
  });
  it("should properly convert numbers smaller than 1", () => {
    const converted = diemAmountToHumanFriendly(1);
    expect(converted).toBe("0.000001");
  });
});

describe("Fiat visual to internal conversions", () => {
  it("should be integer", () => {
    const converted = fiatFromHumanFriendly("123456.123456");
    expect(Number.isInteger(converted));
  });
  it("should be properly scaled", () => {
    const converted = fiatFromHumanFriendly("123456.123456");
    expect(converted).toBe(123456123456);
  });
  it("should be properly scaled even if not a fraction", () => {
    const converted = fiatFromHumanFriendly("123456");
    expect(converted).toBe(123456000000);
  });
  it("should be rounded if too many decimal digits", () => {
    const converted = fiatFromHumanFriendly("123456.123456789");
    expect(converted).toBe(123456123457);
  });
});

describe("Fiat internal to visual conversions", () => {
  it("should be a decimal fraction", () => {
    const converted = fiatToDiemHumanFriendly(123456123456);
    expect(converted).toBe("123456.12");
  });
  it("should add thousands group to big numbers", () => {
    const converted = fiatToDiemHumanFriendly(123456123456, true);
    expect(converted).toBe("123,456.12");
  });
  it("should properly convert integer numbers", () => {
    const converted = fiatToDiemHumanFriendly(123456000000);
    expect(converted).toBe("123456.00");
  });
  it("should properly convert fractions smaller than 1", () => {
    const converted = fiatToDiemHumanFriendly(10000);
    expect(converted).toBe("0.01");
  });
  it("should properly convert numbers smaller than fraction to zero", () => {
    const converted = fiatToDiemHumanFriendly(1);
    expect(converted).toBe("0.00");
  });
});

describe("Fiat rate internal to visual conversions", () => {
  it("should be a decimal fraction", () => {
    const converted = fiatToHumanFriendlyRate(123456123456);
    expect(converted).toBe("123456.1235");
  });
  it("should properly convert integer numbers", () => {
    const converted = fiatToHumanFriendlyRate(123456000000);
    expect(converted).toBe("123456.0000");
  });
  it("should properly convert fractions smaller than 1", () => {
    const converted = fiatToHumanFriendlyRate(10000);
    expect(converted).toBe("0.0100");
  });
  it("should properly convert numbers smaller than fraction to zero", () => {
    const converted = fiatToHumanFriendlyRate(1);
    expect(converted).toBe("0.0000");
  });
});
