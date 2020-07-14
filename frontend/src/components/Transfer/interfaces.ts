// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, LibraCurrency } from "../../interfaces/currencies";

export interface DepositData extends Record<string, any> {
  fundingSource?: number;
  fiatCurrency: FiatCurrency;
  libraCurrency?: LibraCurrency;
  libraAmount?: number;
}

export interface WithdrawData extends Record<string, any> {
  fundingSource?: number;
  fiatCurrency: FiatCurrency;
  libraCurrency?: LibraCurrency;
  libraAmount?: number;
}

export interface ConvertData extends Record<string, any> {
  fromLibraCurrency?: LibraCurrency;
  toLibraCurrency?: LibraCurrency;
  libraAmount?: number;
}
