// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Text } from "react-native-elements";

const NetworkIndicator = () => (
  <Text style={{ fontSize: 12 }}>
    Running on <Text style={{ fontSize: 12, fontWeight: "bold" }}>Testnet</Text>
  </Text>
);

export default NetworkIndicator;
