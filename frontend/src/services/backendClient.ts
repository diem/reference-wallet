// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import axios, { AxiosError, AxiosInstance } from "axios";
import SessionStorage from "../services/sessionStorage";
import { BackendError, ErrorMessage, UsernameAlreadyExistsError } from "./errors";
import { PaymentMethod, User, UserInfo } from "../interfaces/user";
import { Account, CurrencyBalance } from "../interfaces/account";
import { Transaction, TransactionDirection } from "../interfaces/transaction";
import { FiatCurrency, Currency } from "../interfaces/currencies";
import { Quote, QuoteAction, Rate } from "../interfaces/cico";
import { Debt } from "../interfaces/settlement";
import { Chain } from "../interfaces/system";

export default class BackendClient {
  private client: AxiosInstance;

  constructor() {
    const baseURL = process.env.REACT_APP_BACKEND_URL || "/api";
    this.client = axios.create({
      baseURL,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${SessionStorage.getAccessToken()}`,
      },
    });
  }

  // Authentication

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

  // User

  async getUser(): Promise<User> {
    try {
      const response = await this.client.get("/user");
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

  async changeUserPassword(old_password: string, new_password: string): Promise<void> {
    try {
      await this.client.post("/user/actions/change_password", {
        old_password,
        new_password,
      });
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

  // Account

  async getAccount(): Promise<Account> {
    try {
      const response = await this.client.get("/account");
      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async createReceivingAddress(): Promise<string> {
    try {
      const response = await this.client.post("/account/receiving-addresses");
      return response.data.address;
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

  async getTransactions(
    currency?: Currency,
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
    currency: Currency,
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

  // CICO

  async requestDepositQuote(
    fromFiatCurrency: FiatCurrency,
    toCurrency: Currency,
    amount: number
  ): Promise<Quote> {
    return this.requestQuote("buy", toCurrency, fromFiatCurrency, amount);
  }

  async requestWithdrawQuote(
    fromCurrency: Currency,
    toFiatCurrency: FiatCurrency,
    amount: number
  ): Promise<Quote> {
    return this.requestQuote("sell", fromCurrency, toFiatCurrency, amount);
  }

  async requestConvertQuote(
    fromCurrency: Currency,
    toCurrency: Currency,
    amount: number
  ): Promise<Quote> {
    return this.requestQuote("sell", fromCurrency, toCurrency, amount);
  }

  private async requestQuote(
    action: QuoteAction,
    baseCurrency: Currency,
    quoteCurrency: Currency | FiatCurrency,
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

  // Admin

  async getUsers(admin: boolean): Promise<User[]> {
    try {
      const response = await this.client.get(`/admin/users?admin=${admin}`);
      return response.data.users;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getUsersCount(): Promise<number> {
    try {
      const response = await this.client.get("/admin/users/count");
      return response.data.user_count;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async createAdminUser(
    firstName: string,
    lastName: string,
    username: string,
    password: string
  ): Promise<void> {
    try {
      await this.client.post("/admin/users", {
        username: username,
        first_name: firstName,
        last_name: lastName,
        is_admin: true,
        password: password,
      });
    } catch (e) {
      if (e.response?.status === 409) {
        throw new UsernameAlreadyExistsError();
      }
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getWalletTotalBalances(): Promise<CurrencyBalance[]> {
    try {
      const response = await this.client.get("/admin/total-balances");
      return response.data.balances;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async blockUser(user_id: number) {
    try {
      await this.client.put(`/admin/users/${user_id}`);
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async getPendingSettlement(): Promise<Debt[]> {
    try {
      const response = await this.client.get("/admin/settlement");
      return response.data.debt;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  async settleDebts(debts: string[], settlementConfirmation: string) {
    const data = { settlement_confirmation: settlementConfirmation };

    try {
      for (const debt of debts) {
        await this.client.put(`/admin/settlement/${debt}`, data);
      }
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }

  private static handleError(e: AxiosError<ErrorMessage>) {
    if (e.isAxiosError) {
      throw new BackendError(
        e.response?.data.error || `Unexpected error occurred (${e.response?.status})`,
        e.response?.data.code || e.response?.status || 0
      );
    }
  }

  async getChain(): Promise<Chain> {
    try {
      const response = await this.client.get("/network");

      return response.data;
    } catch (e) {
      BackendClient.handleError(e);
      throw e;
    }
  }
}
