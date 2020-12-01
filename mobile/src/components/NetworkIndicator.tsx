// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { View } from "react-native";
import { Text } from "react-native-elements";
// @ts-ignore
import BackArrow from "../assets/back-arrow.svg";

interface NetworkIndicatorProps {
  showBack: boolean;
  onBackPress: () => void;
}

const NetworkIndicator = ({ showBack, onBackPress }: NetworkIndicatorProps) => (
  <View style={{ flexDirection: "row", alignItems: "center" }}>
    {showBack && <BackArrow style={{ marginRight: 16 }} onPress={onBackPress} />}
    <Text style={{ fontSize: 12 }}>
      Running on <Text style={{ fontSize: 12, fontWeight: "bold" }}>Testnet</Text>
    </Text>
  </View>
);

export default NetworkIndicator;
