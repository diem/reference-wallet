// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

export function classNames(classes: object): string {
  return Object.entries(classes)
    .filter((e) => e[1])
    .map((e) => e[0])
    .join(" ");
}
