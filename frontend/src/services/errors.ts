// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

export interface ErrorMessage {
  error: string;
  code: number;
}

export class BackendError extends Error {
  constructor(message: string, public httpStatus: number) {
    super(message);
  }
}

export class UsernameAlreadyExistsError extends Error {}
