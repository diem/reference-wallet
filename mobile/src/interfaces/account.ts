// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { LibraCurrency } from "./currencies";

export interface LibraCurrencyBalance {
  currency: LibraCurrency;
  balance: number;
}

export interface Account {
  balances: LibraCurrencyBalance[];
}
