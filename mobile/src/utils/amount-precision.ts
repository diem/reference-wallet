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
 * Convert the Diem amount from its internal representation to a human
 * readable decimal fraction.
 *
 * Diem amounts are handled internally as fixed point scaled numbers and are
 * converted to decimal fraction only for UI presentation.
 *
 * @param amount  Fixed point scaled Diem amount.
 * @param useGrouping  Group thousands separated with comma.
 */
export function diemToHumanFriendly(amount: number, useGrouping: boolean = false): string {
  return diemToFloat(amount).toLocaleString(undefined, { ...LIBRA_VISUAL_FORMAT, useGrouping });
}

/**
 * Convert the Diem amount from a human readable decimal fraction
 * representation to the fixed point internal format.
 *
 * Diem amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  String containing Diem amount as a decimal fraction.
 */
export function diemFromHumanFriendly(amount: string): number {
  return diemFromFloat(Number.parseFloat(amount));
}

/**
 * Convert the Diem amount from a floating point number representation
 * to the fixed point internal format.
 *
 * Diem amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  Diem amount as a floating point number.
 */
export function diemFromFloat(amount: number): number {
  return Math.round(amount * LIBRA_SCALING_FACTOR);
}

export function diemToFloat(amount: number): number {
  return Math.trunc(amount) / LIBRA_SCALING_FACTOR;
}

export function normalizeDiem(amount: number): number {
  return diemToFloat(diemFromFloat(amount));
}
