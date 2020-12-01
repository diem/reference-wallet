// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

export function shortenDiemAddress(address: string): string {
  const len = 6;
  return address.substr(0, len) + "...." + address.substr(len * -1);
}
