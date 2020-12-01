// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import ContentLoader from "react-content-loader";

function VerifyLoader() {
  return (
    <div className="text-center">
      <ContentLoader
        speed={3}
        width={300}
        height={530}
        viewBox="0 0 300 530"
        backgroundColor="#f3f3f3"
        foregroundColor="#ecebeb"
      >
        <rect x="0" y="0" rx="3" ry="3" width="300" height="30" />
        <rect x="0" y="50" rx="3" ry="3" width="300" height="16" />
        <rect x="0" y="70" rx="3" ry="3" width="300" height="16" />
        <rect x="0" y="90" rx="3" ry="3" width="300" height="16" />
        <rect x="0" y="110" rx="3" ry="3" width="300" height="16" />
        <rect x="0" y="150" rx="3" ry="3" width="300" height="45" />
        <rect x="0" y="219" rx="3" ry="3" width="300" height="45" />
        <rect x="0" y="288" rx="3" ry="3" width="300" height="45" />
        <rect x="0" y="357" rx="3" ry="3" width="300" height="45" />
        <rect x="0" y="426" rx="3" ry="3" width="300" height="45" enableBackground="#000000" />
      </ContentLoader>
    </div>
  );
}

export default VerifyLoader;
