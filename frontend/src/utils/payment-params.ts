// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0
import { parse as uuidParse, stringify as uuidStringify } from "uuid";
import { PaymentInfo } from "../interfaces/payment_info";

export class PaymentParamError extends Error {}

export enum CheckoutDataType {
  PAYMENT_REQUEST = "PAYMENT_REQUEST",
}

export enum PaymentAction {
  AUTHORIZATION = "AUTHORIZATION",
  CHARGE = "CHARGE",
}

export class PaymentParams {
  constructor(
    readonly isFull: boolean,
    readonly vaspAddress: string,
    readonly referenceId: string,
    readonly merchantName?: string,
    readonly checkoutDataType?: CheckoutDataType,
    readonly action?: PaymentAction,
    readonly currency?: string,
    readonly amount?: number,
    readonly expiration?: Date,
    readonly redirectUrl?: string
  ) {}

  public static fromUrlQueryString(queryString: string): PaymentParams {
    const params = new URLSearchParams(queryString);
    let isStandard = false;

    const vaspAddress = PaymentParams.getParam(params, "vaspAddress");
    const referenceId = PaymentParams.getParam(params, "referenceId");

    if (Array.from(params).length === 2) {
      isStandard = true;
    }

    const redirectUrl = PaymentParams.getParam(params, "redirectUrl");

    try {
      new URL(redirectUrl);
    } catch (e) {
      throw new PaymentParamError("redirectUrl contains invalid URL");
    }

    if (Array.from(params).length === 3 || isStandard) {
      return new PaymentParams(
        false,
        vaspAddress,
        referenceId,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        redirectUrl
      );
    }

    const merchantName = PaymentParams.getParam(params, "merchantName");
    const checkoutDataType = CheckoutDataType[PaymentParams.getParam(params, "checkoutDataType")];
    const action = PaymentAction[PaymentParams.getParam(params, "action")];
    const currency = PaymentParams.getParam(params, "currency");
    const amountTxt = PaymentParams.getParam(params, "amount");
    const expirationTxt = PaymentParams.getParam(params, "expiration");

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

    if (action !== PaymentAction.CHARGE) {
      throw new PaymentParamError("action contains invalid value");
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
      true,
      vaspAddress,
      referenceId,
      merchantName,
      checkoutDataType,
      action,
      currency,
      amount,
      new Date(expiration),
      redirectUrl
    );
  }

  private static getParam(searchParams: URLSearchParams, paramName: string): string {
    const value = searchParams.get(paramName);
    if (!value) {
      throw new PaymentParamError(`Parameter ${paramName} not found in the URL query string`);
    }
    return value;
  }

  static fromPaymentInfo(paymentInfo: PaymentInfo, redirectUrl?: string) {
    return new PaymentParams(
      true,
      paymentInfo.vasp_address,
      paymentInfo.reference_id,
      paymentInfo.merchant_name,
      CheckoutDataType.PAYMENT_REQUEST,
      PaymentAction[paymentInfo.action],
      paymentInfo.currency,
      paymentInfo.amount,
      new Date(paymentInfo.expiration),
      redirectUrl
    );
  }
}

function testUuid(uuid: string) {
  uuidStringify(uuidParse(uuid));
}
