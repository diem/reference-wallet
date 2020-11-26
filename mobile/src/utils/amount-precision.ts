// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

const FIAT_MAX_FRACTION_DIGITS = 6;
const FIAT_SCALING_FACTOR = Math.pow(10, FIAT_MAX_FRACTION_DIGITS);
const LIBRA_MAX_FRACTION_DIGITS = 6;
const LIBRA_SCALING_FACTOR = Math.pow(10, LIBRA_MAX_FRACTION_DIGITS);

const FIAT_VISUAL_FORMAT = {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
};

const FIAT_RATE_VISUAL_FORMAT = {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
};

const LIBRA_VISUAL_FORMAT = {
  minimumFractionDigits: 0,
  maximumFractionDigits: LIBRA_MAX_FRACTION_DIGITS,
};

/**
 * Convert the fiat amount from its internal representation to a human
 * readable decimal fraction.
 *
 * Fiat amounts are handled internally as fixed point scaled numbers and are
 * converted to decimal fraction only for UI presentation.
 *
 * @param amount  Fixed point scaled fiat amount.
 * @param useGrouping  Group thousands separated with comma.
 */
export function fiatToHumanFriendly(amount: number, useGrouping: boolean = false): string {
  return fiatToFloat(amount).toLocaleString(undefined, { ...FIAT_VISUAL_FORMAT, useGrouping });
}

export function fiatToHumanFriendlyRate(amount: number): string {
  return fiatToFloat(amount).toLocaleString(undefined, {
    ...FIAT_RATE_VISUAL_FORMAT,
    useGrouping: false,
  });
}

/**
 * Convert the fiat amount from a human readable decimal fraction representation
 * to the fixed point internal format.
 *
 * Fiat amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  String containing fiat amount as a decimal fraction.
 */
export function fiatFromHumanFriendly(amount: string): number {
  return fiatFromFloat(Number.parseFloat(amount));
}

/**
 * Convert the fiat amount from a floating point number representation
 * to the fixed point internal format.
 *
 * Fiat amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  Fixed point scaled fiat amount.
 */
export function fiatFromFloat(amount: number): number {
  return Math.round(amount * FIAT_SCALING_FACTOR);
}

export function fiatToFloat(amount: number): number {
  return Math.trunc(amount) / FIAT_SCALING_FACTOR;
}

/**
 * Convert the Libra amount from its internal representation to a human
 * readable decimal fraction.
 *
 * Libra amounts are handled internally as fixed point scaled numbers and are
 * converted to decimal fraction only for UI presentation.
 *
 * @param amount  Fixed point scaled Libra amount.
 * @param useGrouping  Group thousands separated with comma.
 */
export function libraToHumanFriendly(amount: number, useGrouping: boolean = false): string {
  return libraToFloat(amount).toLocaleString(undefined, { ...LIBRA_VISUAL_FORMAT, useGrouping });
}

/**
 * Convert the Libra amount from a human readable decimal fraction
 * representation to the fixed point internal format.
 *
 * Libra amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  String containing Libra amount as a decimal fraction.
 */
export function libraFromHumanFriendly(amount: string): number {
  return libraFromFloat(Number.parseFloat(amount));
}

/**
 * Convert the Libra amount from a floating point number representation
 * to the fixed point internal format.
 *
 * Libra amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  Libra amount as a floating point number.
 */
export function libraFromFloat(amount: number): number {
  return Math.round(amount * LIBRA_SCALING_FACTOR);
}

export function libraToFloat(amount: number): number {
  return Math.trunc(amount) / LIBRA_SCALING_FACTOR;
}

export function normalizeLibra(amount: number): number {
  return libraToFloat(libraFromFloat(amount));
}
