// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

export interface BlockchainTransaction {
  version: number;
  status: string;
  expirationTime: string;
  source: string;
  destination: string;
  amount: number;
  sequenceNumber: number;
}
