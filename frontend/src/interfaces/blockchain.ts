// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

export const LIBRA_ADDR_PROTOCOL_PREFIX = "libra://";

export interface VASPAccount {
  vasp_name: string;
  user_id: string;
  full_addr: string;
}

export interface BlockchainTransaction {
  version: number;
  status: string;
  expirationTime: string;
  source: string;
  destination: string;
  amount: number;
  sequenceNumber: number;
}
