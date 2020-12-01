// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Link } from "react-router-dom";
import React from "react";

function Breadcrumbs({ pageName }: { pageName: string }) {
  return (
    <nav>
      <div className="container">
        <ol className="breadcrumb">
          <li className="breadcrumb-item">
            <Link to="/">Home</Link>
          </li>
          <li className="breadcrumb-item active" aria-current="page">
            {pageName}
          </li>
        </ol>
      </div>
    </nav>
  );
}

export default Breadcrumbs;
