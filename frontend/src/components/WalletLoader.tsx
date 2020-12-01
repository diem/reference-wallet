// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import ContentLoader from "react-content-loader";

function WalletLoader() {
  return (
    <div className="text-center">
      <ContentLoader
        speed={3}
        width={570}
        height={530}
        viewBox="0 0 570 530"
        backgroundColor="#f3f3f3"
        foregroundColor="#dbdbdb"
      >
        <rect x="219" y="0" rx="3" ry="3" width="50" height="10" />
        <rect x="240" y="60" rx="3" ry="3" width="100" height="30" />
        <rect x="240" y="100" rx="3" ry="3" width="100" height="10" />
        <rect x="284" y="0" rx="3" ry="3" width="75" height="10" />
        <rect x="150" y="171" rx="0" ry="0" width="70" height="32" />
        <rect x="245" y="171" rx="0" ry="0" width="85" height="32" />
        <rect x="350" y="170" rx="0" ry="0" width="90" height="32" />
        <circle cx="40" cy="330" r="15" />
        <rect x="66" y="323" rx="3" ry="3" width="100" height="14" />
        <rect x="500" y="313" rx="3" ry="3" width="50" height="10" />
        <rect x="500" y="333" rx="3" ry="3" width="50" height="7" />
        <circle cx="40" cy="390" r="15" />
        <rect x="66" y="383" rx="3" ry="3" width="100" height="14" />
        <rect x="500" y="373" rx="3" ry="3" width="50" height="10" />
        <rect x="500" y="393" rx="3" ry="3" width="50" height="7" />
        <circle cx="40" cy="450" r="15" />
        <rect x="66" y="443" rx="3" ry="3" width="100" height="14" />
        <rect x="500" y="433" rx="3" ry="3" width="50" height="10" />
        <rect x="500" y="453" rx="3" ry="3" width="50" height="7" />
        <circle cx="40" cy="510" r="15" />
        <rect x="66" y="503" rx="3" ry="3" width="100" height="14" />
        <rect x="500" y="493" rx="3" ry="3" width="50" height="10" />
        <rect x="500" y="513" rx="3" ry="3" width="50" height="7" />
        <rect x="0" y="255" rx="0" ry="0" width="151" height="20" />
      </ContentLoader>
    </div>
  );
}

export default WalletLoader;
