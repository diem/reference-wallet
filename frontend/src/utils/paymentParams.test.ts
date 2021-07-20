// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { PaymentParams, PaymentParamError, CheckoutDataType } from "./payment-params";

describe("Payment params from URL query string", () => {
  describe("All fields are present and have correct values", () => {
    it("should parse successfully", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000Z&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      const params = PaymentParams.fromUrlQueryString(queryString);

      expect(params.vaspAddress).toBe("tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0");
      expect(params.referenceId).toBe("ce74d678-d014-48fc-b61d-2c36683feb29");
      expect(params.merchantName).toBe("merchant-name");
      expect(params.checkoutDataType).toBe(CheckoutDataType.PAYMENT_REQUEST);
      expect(params.action).toBe("CHARGE");
      expect(params.amount).toBe(1000000000);
      expect(params.currency).toBe("XUS");
      expect(params.expiration!.toISOString()).toBe("2020-01-21T00:00:00.000Z");
      expect(params.redirectUrl).toBe(
        "https://merchant.com/order/93c4963f-7f9e-4f9d-983e-7080ef782534/checkout/complete"
      );
    });
  });

  describe("Valid standard payment URL", () => {
    it("should parse successfully", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&redirectUrl=https://www.ynet.co.il/&demo=true";

      const params = PaymentParams.fromUrlQueryString(queryString);

      expect(params.vaspAddress).toBe("tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0");
      expect(params.referenceId).toBe("ce74d678-d014-48fc-b61d-2c36683feb29");
      expect(params.redirectUrl).toBe("https://www.ynet.co.il/");
    });
  });

  describe("Invalid standard payment URL", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&redirectUrl=https://www.ynet.co.il/&demo=true";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("merchantName");
    });
  });

  describe("referenceId is not a proper UUID", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d--2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000Z&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("referenceId");
    });
  });

  describe("amount is not a number", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=rrr100000xxx0000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000Z&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("amount");
    });
  });

  describe("redirectUrl is wrongly encoded", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000Z&" +
        "redirectUrl=https%!3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("redirectUrl");
    });
  });

  describe("redirectUrl contains malformed URL", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000Z&" +
        "redirectUrl=merchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("redirectUrl");
    });
  });

  describe("checkoutDataType contains wrong value", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=__PAYMENT__&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000Z&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("checkoutDataType");
    });
  });

  describe("expiration is a number", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=20000000&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("expiration");
    });
  });

  describe("expiration is not an ISO 8601 date", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=01/01/2020&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("expiration");
    });
  });

  describe("expiration is not in UTC", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=CHARGE&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000%2B0200&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("expiration");
    });
  });

  describe("action is not in CHARGE", () => {
    it("should throw PaymentParamError", () => {
      const queryString =
        "?vaspAddress=tdm1pgyne6my63v9j0ffwfnvn76mq398909f85gys03crzuwv0&" +
        "referenceId=ce74d678-d014-48fc-b61d-2c36683feb29&" +
        "merchantName=merchant-name&" +
        "checkoutDataType=PAYMENT_REQUEST&" +
        "action=DOG&" +
        "amount=1000000000&" +
        "currency=XUS&" +
        "expiration=2020-01-21T00%3A00%3A00.000%2B0200&" +
        "redirectUrl=https%3A%2F%2Fmerchant.com%2Forder%2F93c4963f-7f9e-4f9d-983e-7080ef782534%2Fcheckout%2Fcomplete";

      expect(() => PaymentParams.fromUrlQueryString(queryString)).toThrow("action");
    });
  });
});
