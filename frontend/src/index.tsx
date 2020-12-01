// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import ReactDOM from "react-dom";
import App from "./App";

export const isProd = process.env.NODE_ENV === "production";

ReactDOM.render(<App />, document.getElementById("root"));
