// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0
import { parse as uuidParse, stringify as uuidStringify } from 'uuid';

export class PaymentParamError extends Error {}

export enum CheckoutDataType {
  PAYMENT_REQUEST = "PAYMENT_REQUEST",
}

export class PaymentParams {
  constructor(
    readonly vaspAddress: string,
    readonly referenceId: string,
    readonly merchantName: string,
    readonly checkoutDataType: CheckoutDataType,
    readonly action: string,
    readonly currency: string,
    readonly amount: number,
    readonly expiration: Date,
    readonly redirectUrl: string,
  ) {
  }

  public static fromUrlQueryString(queryString: string): PaymentParams {
    const params = new URLSearchParams(queryString);

    const vaspAddress = PaymentParams.getParam(params, "vaspAddress");
    const merchantName = PaymentParams.getParam(params, "merchantName");
    const checkoutDataType = CheckoutDataType[PaymentParams.getParam(params, "checkoutDataType")];
    const action = PaymentParams.getParam(params, "action");
    const currency = PaymentParams.getParam(params, "currency");
    const amountTxt = PaymentParams.getParam(params, "amount");
    const expirationTxt = PaymentParams.getParam(params, "expiration");
    const redirectUrl = PaymentParams.getParam(params, "redirectUrl");
    const referenceId = PaymentParams.getParam(params, "referenceId");

    try {
      new URL(redirectUrl);
    } catch (e) {
      throw new PaymentParamError("redirectUrl contains invalid URL");
    }

    try {
      testUuid(referenceId);
    } catch (e) {
      throw new PaymentParamError("referenceId contains invalid UUID");
    }

    const amount = Number(amountTxt).valueOf();
    if (!amount) {
      throw new PaymentParamError("amount contains invalid number");
    }

    if (checkoutDataType !== CheckoutDataType.PAYMENT_REQUEST) {
      throw new PaymentParamError("checkoutDataType contains invalid value");
    }

    const expiration = new Date(expirationTxt);
    try {
      expiration.toISOString();
    } catch (e) {
      throw new PaymentParamError("expiration contains invalid date");
    }
    if (expiration.toISOString() !== expirationTxt) {
      throw new PaymentParamError("expiration contains invalid date");
    }

    return new PaymentParams(
      vaspAddress,
      referenceId,
      merchantName,
      checkoutDataType,
      action,
      currency,
      amount,
      new Date(expiration),
      redirectUrl,
    );
  }

  private static getParam(searchParams: URLSearchParams, paramName: string): string {
    const value = searchParams.get(paramName);
    if (!value) {
      throw new PaymentParamError(`Parameter ${paramName} not found in the URL query string`);
    }
    return value;
  }
}

function testUuid(uuid: string) {
  uuidStringify(uuidParse(uuid));
}
