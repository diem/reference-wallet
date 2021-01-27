// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, DiemCurrency } from "../../interfaces/currencies";

export interface Send {
  currency?: DiemCurrency;
  fiatCurrency: FiatCurrency;
  amount?: number;
  address?: string;
}
