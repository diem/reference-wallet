// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Moment } from "moment";
import { FiatCurrency } from "./currencies";

export enum RegistrationStatus {
  Registered = "Registered",
  Verified = "Verified",
  Pending = "Pending",
  Approved = "Approved",
  Rejected = "Rejected",
}

export type PaymentMethodProviders = "BankAccount" | "CreditCard";

export const paymentMethodsLabels: { [key in PaymentMethodProviders]: string } = {
  BankAccount: "Bank Account",
  CreditCard: "Credit Card",
};

export interface PaymentMethod {
  id: number;
  name: string;
  provider: PaymentMethodProviders;
  token: string;
}

export type NewPaymentMethod = Pick<PaymentMethod, "name" | "provider" | "token">;

export interface UserInfo {
  selected_fiat_currency: FiatCurrency;
  selected_language: string;
  first_name: string;
  last_name: string;
  dob: Moment | string;
  phone: string;
  country?: string;
  address_1: string;
  address_2: string;
  city: string;
  state: string;
  zip: string;
}

export interface User extends UserInfo {
  id: number;
  username: string;
  is_admin: boolean;
  is_blocked: boolean;
  registration_status: RegistrationStatus;
}
