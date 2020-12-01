// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

class SessionStorage {
  storeAccessToken(token: string): void {
    window.localStorage.setItem("token", token);
  }

  getAccessToken(): string | undefined {
    const token = window.localStorage.getItem("token");
    if (!token) {
      return undefined;
    }
    return token;
  }

  removeAccessToken(): void {
    window.localStorage.removeItem("token");
  }
}

export default new SessionStorage();
