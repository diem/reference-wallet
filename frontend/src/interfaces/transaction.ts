// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Currency } from "./currencies";
import { BlockchainTransaction, VASPAccount } from "./blockchain";

export type TransactionDirection = "received" | "sent";

export type TransactionStatus = "completed" | "pending" | "canceled";

export interface Transaction {
  id: number;
  direction: TransactionDirection;
  status: TransactionStatus;
  currency: Currency;
  source: VASPAccount;
  destination: VASPAccount;
  amount: number;
  blockchain_tx?: BlockchainTransaction;
  timestamp: string;
  is_internal: boolean;
}
