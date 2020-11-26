// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { BlockchainTransaction } from "../interfaces/blockchain";

// FIXME: DIEM
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
    <a href={blockExplorerUrl} target="_blank" rel="noopener noreferrer" className="hover">
      {blockchainTx.version}
      <i className="fa fa-external-link small hover-hide" />
    </a>
  );
}

export default ExplorerLink;
