// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { DiemCurrency } from "./currencies";

export interface CurrencyBalance {
  currency: DiemCurrency;
  balance: number;
}

export interface Account {
  balances: CurrencyBalance[];
}
