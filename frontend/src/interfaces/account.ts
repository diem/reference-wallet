// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Currency } from "./currencies";

export interface CurrencyBalance {
  currency: Currency;
  balance: number;
}

export interface Account {
  balances: CurrencyBalance[];
}
