// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import AsyncStorage from "@react-native-community/async-storage";

class SessionStorage {
  async storeAccessToken(token: string): Promise<void> {
    await AsyncStorage.setItem("token", token);
  }

  async getAccessToken(): Promise<string | undefined> {
    const token = await AsyncStorage.getItem("token");
    if (!token) {
      return undefined;
    }
    return token;
  }

  async removeAccessToken(): Promise<void> {
    await AsyncStorage.removeItem("token");
  }
}

export default new SessionStorage();
