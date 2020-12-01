// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

const FIAT_MAX_FRACTION_DIGITS = 6;
const FIAT_SCALING_FACTOR = Math.pow(10, FIAT_MAX_FRACTION_DIGITS);
const DIEM_MAX_FRACTION_DIGITS = 6;
const DIEM_SCALING_FACTOR = Math.pow(10, DIEM_MAX_FRACTION_DIGITS);

const FIAT_VISUAL_FORMAT = {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
};

const FIAT_RATE_VISUAL_FORMAT = {
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
};

const DIEM_VISUAL_FORMAT = {
  minimumFractionDigits: 0,
  maximumFractionDigits: DIEM_MAX_FRACTION_DIGITS,
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
export function fiatToDiemHumanFriendly(amount: number, useGrouping: boolean = false): string {
  return fiatToDiemFloat(amount).toLocaleString(undefined, { ...FIAT_VISUAL_FORMAT, useGrouping });
}

export function fiatToHumanFriendlyRate(amount: number): string {
  return fiatToDiemFloat(amount).toLocaleString(undefined, {
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
  return fiatFromDiemFloat(Number.parseFloat(amount));
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
export function fiatFromDiemFloat(amount: number): number {
  return Math.round(amount * FIAT_SCALING_FACTOR);
}

export function fiatToDiemFloat(amount: number): number {
  return Math.trunc(amount) / FIAT_SCALING_FACTOR;
}

/**
 * Convert the amount from its internal representation to a human
 * readable decimal fraction.
 *
 * amounts are handled internally as fixed point scaled numbers and are
 * converted to decimal fraction only for UI presentation.
 *
 * @param amount  Fixed point scaled amount.
 * @param useGrouping  Group thousands separated with comma.
 */
export function diemAmountToHumanFriendly(amount: number, useGrouping: boolean = false): string {
  return diemAmountToFloat(amount).toLocaleString(undefined, {
    ...DIEM_VISUAL_FORMAT,
    useGrouping,
  });
}

/**
 * Convert the amount from a human readable decimal fraction
 * representation to the fixed point internal format.
 *
 * amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount  String containing amount as a decimal fraction.
 */
export function diemAmountFromHumanFriendly(amount: string): number {
  return diemAmountFromFloat(Number.parseFloat(amount));
}

/**
 * Convert the amount from a floating point number representation
 * to the fixed point internal format.
 *
 * amounts are handled internally as fixed point scaled numbers
 * and are converted to decimal fraction only for UI presentation.
 *
 * @param amount amount as a floating point number.
 */
export function diemAmountFromFloat(amount: number): number {
  return Math.round(amount * DIEM_SCALING_FACTOR);
}

export function diemAmountToFloat(amount: number): number {
  return Math.trunc(amount) / DIEM_SCALING_FACTOR;
}

export function normalizeDiemAmount(amount: number): number {
  return diemAmountToFloat(diemAmountFromFloat(amount));
}
