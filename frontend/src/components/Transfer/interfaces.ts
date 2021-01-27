// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, DiemCurrency } from "../../interfaces/currencies";

export interface DepositData extends Record<string, any> {
  fundingSource?: number;
  fiatCurrency: FiatCurrency;
  currency?: DiemCurrency;
  amount?: number;
}

export interface WithdrawData extends Record<string, any> {
  fundingSource?: number;
  fiatCurrency: FiatCurrency;
  currency?: DiemCurrency;
  amount?: number;
}

export interface ConvertData extends Record<string, any> {
  fromCurrency?: DiemCurrency;
  toCurrency?: DiemCurrency;
  amount?: number;
}
