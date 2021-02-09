// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { DiemCurrency } from "./currencies";

type ApprovalStatus = "pending" | "valid" | "rejected" | "closed";

type ScopeType = "consent" | "save_sub_account";

type UnitType = "day" | "week" | "month" | "year";

export interface Approval {
  address: string;
  biller_address: string;
  funds_pull_pre_approval_id: string;
  scope: Scope;
  description: string;
  status: ApprovalStatus;
  biller_name: string;
  created_at: string;
  updated_at: string;
  approved_at: string;
}

interface Scope {
  type: ScopeType;
  expiration_timestamp: number;
  max_cumulative_amount: ScopedCumulativeAmount;
  max_transaction_amount: Currency;
}

interface ScopedCumulativeAmount {
  unit: UnitType;
  value: number;
  max_amount: Currency;
}

interface Currency {
  amount: number;
  currency: DiemCurrency;
}
