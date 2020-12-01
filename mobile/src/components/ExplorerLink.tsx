// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { BlockchainTransaction } from "../interfaces/blockchain";
import { Text, ThemeConsumer } from "react-native-elements";
import React from "react";
import { Linking, TouchableOpacity } from "react-native";
import { appTheme } from "../styles";

// @ts-ignore
const EXPLORER_URL_FORMAT =
  process.env.REACT_APP_EXPLORER_URL || "https://librabrowser.io/version/{version}";

interface ExplorerLinkProps {
  blockchainTx: BlockchainTransaction;
}

function ExplorerLink({ blockchainTx }: ExplorerLinkProps) {
  const blockExplorerUrl = EXPLORER_URL_FORMAT.replace(
    "{version}",
    blockchainTx.version.toString()
  );
  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <TouchableOpacity onPress={() => Linking.openURL(blockExplorerUrl)}>
          <Text style={{ color: theme.colors!.primary }}>{blockchainTx.version}</Text>
        </TouchableOpacity>
      )}
    </ThemeConsumer>
  );
}

export default ExplorerLink;
