// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import axios, { AxiosError, AxiosInstance } from "axios";
import { BackendError, ErrorMessage } from "./errors";
import { PaymentMethod, User, UserInfo } from "../interfaces/user";
import { Quote, QuoteAction, Rate } from "../interfaces/cico";
import { Account } from "../interfaces/account";
import { FiatCurrency, DiemCurrency } from "../interfaces/currencies";
import { Transaction, TransactionDirection } from "../interfaces/transaction";

export default class BackendClient {
  private client: AxiosInstance;

  constructor(access_token?: string) {
    // @ts-ignore
    const baseURL = process.env.BACKEND_URL || "https://demo-wallet.diem.com/api";
    this.client = axios.create({
      baseURL,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access_token}`,
      },
    });
  }

  private static handleError(e: AxiosError<ErrorMessage>) {
    if (e.isAxiosError) {
      const message = e.response?.data.error || `Unexpected error occurred (${e.response?.status})`;
      const status = e.response?.status || 0;

      console.log("Backend Error", { message, status });
      throw new BackendError(message, status);
    }
  }

  async signupUser(username: string, password: string): Promise<string> {
    try {
      const response = await this.client.post("/user", { username, password });
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async signinUser(username: string, password: string): Promise<string> {
    try {
      const response = await this.client.post("/user/actions/signin", {
        username,
        password,
      });
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async signoutUser(): Promise<void> {
    try {
      await this.client.post("/user/actions/signout");
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getUser(): Promise<User> {
    try {
      const response = await this.client.get("/user");
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async updateUserInfo(userInfo: UserInfo): Promise<User> {
    try {
      userInfo.dob =
        typeof userInfo.dob === "string" ? userInfo.dob : userInfo.dob.format("YYYY-MM-DD");
      const response = await this.client.put("/user", userInfo);
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async updateUserSettings(
    selected_language: string,
    selected_fiat_currency: FiatCurrency
  ): Promise<User> {
    try {
      const response = await this.client.put("/user", {
        selected_language,
        selected_fiat_currency,
      });
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async refreshUser(): Promise<void> {
    try {
      await this.client.post("/user/actions/refresh");
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async forgotPassword(username: string): Promise<string> {
    try {
      const response = await this.client.post("/user/actions/forgot_password", {
        username,
      });
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async resetUserPassword(token: string, new_password: string): Promise<void> {
    try {
      await this.client.post("/user/actions/reset_password", {
        token,
        new_password,
      });
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getRates(): Promise<Rate[]> {
    try {
      const response = await this.client.get("/account/rates");
      return response.data.rates;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getAccount(): Promise<Account> {
    try {
      const response = await this.client.get("/account");
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getPaymentMethods(): Promise<PaymentMethod[]> {
    try {
      const response = await this.client.get("/user/payment-methods");
      return response.data.payment_methods;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async storePaymentMethod(name: string, provider: string, token: string): Promise<void> {
    try {
      await this.client.post("/user/payment-methods", {
        name,
        provider,
        token,
      });
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getTransactions(
    currency?: DiemCurrency,
    direction?: TransactionDirection,
    sort?: string,
    limit?: number
  ): Promise<Transaction[]> {
    try {
      const response = await this.client.get("/account/transactions", {
        params: { currency, direction, sort, limit },
      });
      return response.data.transaction_list;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async createTransaction(
    currency: DiemCurrency,
    amount: number,
    receiver_address: string
  ): Promise<Transaction> {
    try {
      const response = await this.client.post("/account/transactions", {
        currency,
        amount,
        receiver_address,
      });
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  private async requestQuote(
    action: QuoteAction,
    baseCurrency: DiemCurrency,
    quoteCurrency: DiemCurrency | FiatCurrency,
    amount: number
  ): Promise<Quote> {
    try {
      const currencyPair = `${baseCurrency}_${quoteCurrency}`;
      const response = await this.client.post("/account/quotes", {
        action,
        amount,
        currency_pair: currencyPair,
      });
      return {
        quoteId: response.data.quote_id,
        rfq: response.data.rfq,
        price: response.data.price,
        expirationTime: new Date(response.data.expiration_time),
      };
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async requestDepositQuote(
    fromFiatCurrency: FiatCurrency,
    toDiemCurrency: DiemCurrency,
    microdiems: number
  ): Promise<Quote> {
    return this.requestQuote("buy", toDiemCurrency, fromFiatCurrency, microdiems);
  }

  async requestWithdrawQuote(
    fromDiemCurrency: DiemCurrency,
    toFiatCurrency: FiatCurrency,
    microdiems: number
  ): Promise<Quote> {
    return this.requestQuote("sell", fromDiemCurrency, toFiatCurrency, microdiems);
  }

  async requestConvertQuote(
    fromDiemCurrency: DiemCurrency,
    toDiemCurrency: DiemCurrency,
    microdiems: number
  ): Promise<Quote> {
    return this.requestQuote("sell", fromDiemCurrency, toDiemCurrency, microdiems);
  }

  async executeQuote(quoteId: string, paymentMethod?: number): Promise<void> {
    try {
      await this.client.post(`/account/quotes/${quoteId}/actions/execute`, {
        payment_method: paymentMethod,
      });
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async createReceivingAddress(currency?: DiemCurrency): Promise<string> {
    try {
      const response = await this.client.post("/account/receiving-addresses", {
        currency,
      });
      return response.data.address;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }
}
