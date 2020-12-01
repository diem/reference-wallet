// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import SessionStorage from "../services/sessionStorage";
import { Redirect, Route } from "react-router-dom";
import React from "react";

export const LoggedInRoute = ({ component: Component, ...rest }) => {
  const loggedIn = !!SessionStorage.getAccessToken();
  return (
    <Route
      {...rest}
      render={(props) => (loggedIn ? <Component {...rest} {...props} /> : <Redirect to="/login" />)}
    />
  );
};

export const LoggedOutRoute = ({ component: Component, ...rest }) => {
  const loggedOut = !SessionStorage.getAccessToken();
  return (
    <Route
      {...rest}
      render={(props) => (loggedOut ? <Component {...rest} {...props} /> : <Redirect to="/" />)}
    />
  );
};
