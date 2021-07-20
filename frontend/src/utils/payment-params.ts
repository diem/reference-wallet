// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0
import { parse as uuidParse, stringify as uuidStringify } from "uuid";
import { PaymentDetails } from "../interfaces/payment_details";

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
    readonly demo: boolean,
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

    const vaspAddress = PaymentParams.getParam(params, "vaspAddress");
    const referenceId = PaymentParams.getParam(params, "referenceId");

    if (Array.from(params).length === 3) {
      return new PaymentParams(
        false,
        vaspAddress,
        referenceId,
        false,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined
      );
    }

    const redirectUrl = PaymentParams.getParam(params, "redirectUrl");

    try {
      new URL(redirectUrl);
    } catch (e) {
      throw new PaymentParamError("redirectUrl contains invalid URL");
    }

    if (Array.from(params).length === 4) {
      return new PaymentParams(
        false,
        vaspAddress,
        referenceId,
        false,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        undefined,
        redirectUrl
      );
    }

    const demo = PaymentParams.isDemo(params, "demo");
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

    if (action !== PaymentAction.CHARGE && action !== PaymentAction.AUTHORIZATION) {
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
      demo,
      merchantName,
      checkoutDataType,
      action,
      currency,
      amount,
      expiration,
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

  private static isDemo(searchParams: URLSearchParams, paramName: string): boolean {
    if (searchParams.has(paramName)) {
      const value = searchParams.get(paramName);
      if (value?.toLowerCase() === "true") {
        return true;
      }
    }
    return false;
  }

  static fromPaymentDetails(paymentInfo: PaymentDetails, redirectUrl?: string) {
    return new PaymentParams(
      true,
      paymentInfo.vasp_address,
      paymentInfo.reference_id,
      paymentInfo.demo,
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
