// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import moment from "moment";
import { PaymentMethod, RegistrationStatus, User, UserInfo } from "../interfaces/user";
import { Account } from "../interfaces/account";
import { Transaction } from "../interfaces/transaction";
import { Rate } from "../interfaces/cico";

export const testToken = "TOP SECRET";

export const userInfo: UserInfo = {
  selected_fiat_currency: "USD",
  selected_language: "en",
  first_name: "Sherlock",
  last_name: "Holmes",
  dob: moment("1861-06-01"),
  phone: "44 2079460869",
  country: "GB",
  state: "",
  city: "London",
  address_1: "221B Baker Street",
  address_2: "",
  zip: "NW1 6XE",
};

export const user: User = {
  ...userInfo,
  id: 1,
  username: "test_user",
  is_admin: false,
  is_blocked: false,
  registration_status: RegistrationStatus.Registered,
};

export const paymentMethod: PaymentMethod = {
  id: 0,
  name: "plastic-card",
  provider: "CreditCard",
  token: "some-token",
};

export const rate: Rate = {
  currency_pair: "Coin1",
  price: 1.1,
};

export const account: Account = {
  balances: [],
};

export const transaction: Transaction = {
  id: 0,
  direction: "received",
  status: "completed",
  currency: "Coin1",
  destination: {
    vasp_name: "Some receiving VASP",
    user_id: "user1",
    full_addr: "receiver full addr",
  },
  source: {
    vasp_name: "Some sending VASP",
    user_id: "user2",
    full_addr: "sender full addr",
  },
  amount: 10000,
  timestamp: "",
  blockchain_tx: undefined,
  is_internal: false,
};
