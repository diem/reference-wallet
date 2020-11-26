// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency } from "./currencies";

export interface Debt {
  debt_id: string;
  currency: FiatCurrency;
  amount: number;
}
