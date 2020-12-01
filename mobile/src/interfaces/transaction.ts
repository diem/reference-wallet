// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { LibraCurrency } from "./currencies";
import { BlockchainTransaction } from "./blockchain";

export interface VASPAccount {
  vasp_name: string;
  user_id: string;
  full_addr: string;
}

export type TransactionDirection = "received" | "sent";

export type TransactionStatus = "completed" | "pending" | "canceled";

export interface Transaction {
  id: string;
  direction: TransactionDirection;
  status: TransactionStatus;
  currency: LibraCurrency;
  source: VASPAccount;
  destination: VASPAccount;
  amount: number;
  blockchain_tx?: BlockchainTransaction;
  timestamp: string;
  is_internal: boolean;
}
