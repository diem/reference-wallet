// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import axios, { AxiosResponse } from "axios";
import * as HttpCodes from "http-status-codes";
import BackendClient from "./backendClient";
import SessionStorage from "../services/sessionStorage";
import { FiatCurrency, Currency } from "../interfaces/currencies";
import { Quote, Rate, RequestForQuote } from "../interfaces/cico";
import { PaymentMethod, User } from "../interfaces/user";
import { Account } from "../interfaces/account";
import {
  account,
  paymentMethod,
  rate,
  testToken,
  transaction,
  user,
  userInfo,
} from "../tests/stubs";
import { Transaction } from "../interfaces/transaction";

jest.mock("axios");
const axiosMock = axios as jest.Mocked<typeof axios>;

const ok: AxiosResponse = {
  data: {},
  status: HttpCodes.OK,
  statusText: "OK",
  headers: {},
  config: {},
};

beforeAll(() => {
  axiosMock.create = jest.fn(() => axiosMock);
});

describe("Authentication", () => {
  const username = "test_user";
  const password = "test_password";

  describe("signup", () => {
    let returnedToken: string | undefined;

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: testToken });

      returnedToken = await new BackendClient().signupUser(username, password);
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({ username, password });
    });
    it("returns new session token", () => {
      expect(returnedToken).toBe(testToken);
    });
  });

  describe("signin", () => {
    let returnedToken: string | undefined;

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: testToken });

      returnedToken = await new BackendClient().signinUser(username, password);
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/actions/signin`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({ username, password });
    });
    it("returns new session token", () => {
      expect(returnedToken).toBe(testToken);
    });
  });

  describe("signout", () => {
    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok });

      await new BackendClient().signoutUser();
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/actions/signout`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toBeUndefined();
    });
  });

  describe("forgot password", () => {
    let returnedToken: string | undefined;

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: testToken });

      returnedToken = await new BackendClient().forgotPassword(username);
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/actions/forgot_password`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({
        username: username,
      });
    });
    it("returns new password reset token", () => {
      expect(returnedToken).toBe(testToken);
    });
  });

  describe("reset user password", () => {
    const resetToken = "reset_token";
    const expectedPassword = "new_password";

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: testToken });

      await new BackendClient().resetUserPassword(resetToken, expectedPassword);
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/actions/reset_password`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({
        new_password: expectedPassword,
        token: resetToken,
      });
    });
  });
});

describe("User", () => {
  describe("get user", () => {
    let returnedUser: User | undefined;

    beforeEach(async () => {
      axiosMock.get.mockReset();
      axiosMock.get.mockResolvedValueOnce({ ...ok, data: user });

      returnedUser = await new BackendClient().getUser();
    });

    it("sends GET request", () => {
      expect(axiosMock.get).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.get.mock.calls[0][0]).toBe(`/user`);
    });
    it("returns user data", () => {
      expect(returnedUser).toStrictEqual(user);
    });
  });

  describe("refresh user", () => {
    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: testToken });

      await new BackendClient().refreshUser();
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/actions/refresh`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toBeUndefined();
    });
  });

  describe("update user info", () => {
    const updatedUserInfo = {
      ...userInfo,
      first_name: "New",
      last_name: "Name",
    };
    const updatedUser = {
      ...user,
      ...updatedUserInfo,
    };
    let returnedUser: User | undefined;

    beforeEach(async () => {
      axiosMock.put.mockReset();
      axiosMock.put.mockResolvedValueOnce({ ...ok, data: updatedUser });

      returnedUser = await new BackendClient().updateUserInfo(updatedUserInfo);
    });

    it("sends PUT request", () => {
      expect(axiosMock.put).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.put.mock.calls[0][0]).toBe(`/user`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.put.mock.calls[0][1]).toStrictEqual(updatedUserInfo);
    });
    it("returns updated user data", () => {
      expect(returnedUser).toStrictEqual(updatedUser);
    });
  });

  describe("update user settings", () => {
    const updatedUserSettings = {
      selected_language: "he",
      selected_fiat_currency: "EUR",
    };
    const updatedUser = {
      ...user,
      ...updatedUserSettings,
    };
    let returnedUser: User | undefined;

    beforeEach(async () => {
      axiosMock.put.mockReset();
      axiosMock.put.mockResolvedValueOnce({ ...ok, data: updatedUser });

      returnedUser = await new BackendClient().updateUserSettings("he", "EUR");
    });

    it("sends PUT request", () => {
      expect(axiosMock.put).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.put.mock.calls[0][0]).toBe(`/user`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.put.mock.calls[0][1]).toStrictEqual(updatedUserSettings);
    });
    it("returns updated user data", () => {
      expect(returnedUser).toStrictEqual(updatedUser);
    });
  });

  describe("change user password", () => {
    const oldPassword = "old_password";
    const expectedPassword = "new_password";

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: testToken });

      await new BackendClient().changeUserPassword(oldPassword, expectedPassword);
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/actions/change_password`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({
        old_password: oldPassword,
        new_password: expectedPassword,
      });
    });
  });

  describe("get payment methods", () => {
    let returnedPaymentMethods: PaymentMethod[] | undefined;

    beforeEach(async () => {
      axiosMock.get.mockReset();
      axiosMock.get.mockResolvedValueOnce({ ...ok, data: { payment_methods: [paymentMethod] } });

      returnedPaymentMethods = await new BackendClient().getPaymentMethods();
    });

    it("sends GET request", () => {
      expect(axiosMock.get).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.get.mock.calls[0][0]).toBe(`/user/payment-methods`);
    });
    it("returns payment methods", () => {
      expect(returnedPaymentMethods).toStrictEqual([paymentMethod]);
    });
  });

  describe("store payment methods", () => {
    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok });

      await new BackendClient().storePaymentMethod("test", "SomeBank", "bank-token");
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/user/payment-methods`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({
        name: "test",
        provider: "SomeBank",
        token: "bank-token",
      });
    });
  });
});

describe("Account", () => {
  describe("get account", () => {
    let returnedAccount: Account | undefined;

    beforeEach(async () => {
      axiosMock.get.mockReset();
      axiosMock.get.mockResolvedValueOnce({ ...ok, data: account });

      returnedAccount = await new BackendClient().getAccount();
    });

    it("sends GET request", () => {
      expect(axiosMock.get).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.get.mock.calls[0][0]).toBe(`/account`);
    });
    it("returns user data", () => {
      expect(returnedAccount).toStrictEqual(account);
    });
  });

  describe("create receiving address", () => {
    let returnedAddress: string | undefined;

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: { address: "address" } });

      returnedAddress = await new BackendClient().createReceivingAddress();
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/account/receiving-addresses`);
    });
    it("returns user data", () => {
      expect(returnedAddress).toStrictEqual("address");
    });
  });

  describe("get rates", () => {
    const expectedRates = [rate, { ...rate, price: 1.5 }];
    let returnedRates: Rate[] | undefined;

    beforeEach(async () => {
      axiosMock.get.mockReset();
      axiosMock.get.mockResolvedValueOnce({ ...ok, data: { rates: expectedRates } });

      returnedRates = await new BackendClient().getRates();
    });

    it("sends GET request", () => {
      expect(axiosMock.get).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.get.mock.calls[0][0]).toBe(`/account/rates`);
    });
    it("returns user data", () => {
      expect(returnedRates).toStrictEqual(expectedRates);
    });
  });

  describe("get transactions", () => {
    const expectedTransactions = [transaction];
    let returnedTransactions: Transaction[] | undefined;

    beforeEach(async () => {
      axiosMock.get.mockReset();
      axiosMock.get.mockResolvedValueOnce({
        ...ok,
        data: { transaction_list: expectedTransactions },
      });

      returnedTransactions = await new BackendClient().getTransactions();
    });

    it("sends GET request", () => {
      expect(axiosMock.get).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.get.mock.calls[0][0]).toBe(`/account/transactions`);
    });
    it("returns user data", () => {
      expect(returnedTransactions).toStrictEqual(expectedTransactions);
    });
  });

  describe("create transaction", () => {
    let returnedTransaction: Transaction | undefined;

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: transaction });

      returnedTransaction = await new BackendClient().createTransaction(
        transaction.currency,
        transaction.amount,
        transaction.destination.full_addr
      );
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/account/transactions`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({
        currency: transaction.currency,
        amount: transaction.amount,
        receiver_address: transaction.destination.full_addr,
      });
    });
    it("returns user data", () => {
      expect(returnedTransaction).toStrictEqual(transaction);
    });
  });
});

describe("CICO", () => {
  const fiatCurrency: FiatCurrency = "USD";
  const currency: Currency = "Coin1";
  const currencyPair = "Coin1_USD";
  const amount = 123;
  const quoteId = "MAGNA-QUOTUM";
  const paymentMethod = 1;

  beforeAll(() => {
    SessionStorage.storeAccessToken(testToken);
  });

  describe.each`
    quoteAction | method
    ${"sell"}   | ${async () => new BackendClient().requestWithdrawQuote(currency, fiatCurrency, amount)}
    ${"buy"}    | ${async () => new BackendClient().requestDepositQuote(fiatCurrency, currency, amount)}
  `("$quoteAction quote", ({ quoteAction, method }) => {
    const expectedRequest: RequestForQuote = {
      action: quoteAction,
      amount: amount,
      currency_pair: currencyPair,
    };
    const expectedResponse = {
      quote_id: "1338",
      rfq: expectedRequest,
      price: 456,
      expiration_time: "2020-10-20T12:31:57.820Z",
    };
    const expectedQuote: Quote = {
      quoteId: "1338",
      rfq: expectedRequest,
      price: 456,
      expirationTime: new Date("2020-10-20T12:31:57.820Z"),
    };

    let actualQuote: Quote | undefined;

    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: expectedResponse });

      actualQuote = await method();
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe("/account/quotes");
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual(expectedRequest);
    });
    it("returns correct quote", () => {
      expect(actualQuote).toStrictEqual(expectedQuote);
    });
  });

  describe("execute quote", () => {
    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok });

      await new BackendClient().executeQuote(quoteId, paymentMethod);
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/account/quotes/${quoteId}/actions/execute`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({ payment_method: paymentMethod });
    });
  });
});

describe("Admin", () => {
  describe("get users", () => {
    let returnedUsers: User[] | undefined;

    beforeEach(async () => {
      axiosMock.get.mockReset();
      axiosMock.get.mockResolvedValueOnce({ ...ok, data: { users: [user] } });

      returnedUsers = await new BackendClient().getUsers(true);
    });

    it("sends GET request", () => {
      expect(axiosMock.get).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.get.mock.calls[0][0]).toBe(`/admin/users?admin=true`);
    });
    it("returns user data", () => {
      expect(returnedUsers).toStrictEqual([user]);
    });
  });

  describe("create admin user", () => {
    beforeEach(async () => {
      axiosMock.post.mockReset();
      axiosMock.post.mockResolvedValueOnce({ ...ok, data: user });

      await new BackendClient().createAdminUser(
        user.first_name,
        user.last_name,
        user.username,
        "123"
      );
    });

    it("sends POST request", () => {
      expect(axiosMock.post).toHaveBeenCalledTimes(1);
    });
    it("sends the request to the correct endpoint", () => {
      expect(axiosMock.post.mock.calls[0][0]).toBe(`/admin/users`);
    });
    it("sends correct request data", () => {
      expect(axiosMock.post.mock.calls[0][1]).toStrictEqual({
        username: user.username,
        first_name: user.first_name,
        last_name: user.last_name,
        is_admin: true,
        password: "123",
      });
    });
  });
});
