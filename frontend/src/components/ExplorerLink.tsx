// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { BlockchainTransaction } from "../interfaces/blockchain";
import BackendClient from "../services/backendClient";

const EXPLORER_URL_FORMAT =
  process.env.REACT_APP_EXPLORER_URL ||
  "https://diemexplorer.com/{chainDisplayName}/version/{version}";

interface ExplorerLinkProps {
  blockchainTx: BlockchainTransaction;
}

function ExplorerLink({ blockchainTx }: ExplorerLinkProps) {
  const [chainDisplayName, setChainDisplayName] = useState<string>("testnet");

  useEffect(() => {
    async function getChainDisplayName() {
      try {
        const backendClient = new BackendClient();
        const chain = await backendClient.getChain();
        setChainDisplayName(chain.display_name);
      } catch (e) {
        console.error(e);
      }
    }

    // noinspection JSIgnoredPromiseFromCall
    getChainDisplayName();
  }, []);

  const blockExplorerUrl = EXPLORER_URL_FORMAT.replace(
    "{version}",
    blockchainTx.version.toString()
  ).replace("{chainDisplayName}", chainDisplayName);

  return (
    <a href={blockExplorerUrl} target="_blank" rel="noopener noreferrer" className="hover">
      {blockchainTx.version}
      <i className="fa fa-external-link small hover-hide" />
    </a>
  );
}

export default ExplorerLink;
