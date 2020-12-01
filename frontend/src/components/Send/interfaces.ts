// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, Currency } from "../../interfaces/currencies";

export interface Send {
  currency?: Currency;
  fiatCurrency: FiatCurrency;
  amount?: number;
  address?: string;
}
