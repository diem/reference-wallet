// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

export type QuoteAction = "buy" | "sell";

export interface RequestForQuote {
  action: QuoteAction;
  amount: number;
  currency_pair: string; // FIXME: specify the supported values
}

export interface Quote {
  quoteId: string;
  rfq: RequestForQuote;
  price: number;
  expirationTime: Date;
}

export interface Rate {
  currency_pair: string;
  price: number;
}
