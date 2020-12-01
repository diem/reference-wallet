// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Moment } from "moment";
import { FiatCurrency } from "../../interfaces/currencies";

export interface IdentityInfo extends Record<string, any> {
  first_name: string;
  last_name: string;
  dob: string | Moment;
  phone_prefix: string;
  phone_number: string;
}

export interface CountryInfo extends Record<string, any> {
  country: string;
}

export interface AddressInfo extends Record<string, string> {
  address_1: string;
  address_2: string;
  city: string;
  state: string;
  zip: string;
}

export interface DefaultSettings extends Record<string, any> {
  default_fiat_currency: FiatCurrency;
}
