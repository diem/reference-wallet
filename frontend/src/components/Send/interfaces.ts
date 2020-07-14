// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { FiatCurrency, LibraCurrency } from "../../interfaces/currencies";

export interface Send {
  libraCurrency?: LibraCurrency;
  fiatCurrency: FiatCurrency;
  libraAmount?: number;
  libraAddress?: string;
}
