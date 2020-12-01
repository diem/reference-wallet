// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Alert } from "reactstrap";
import React from "react";

interface ErrorMessageProps {
  message: string;
}

function ErrorMessage({ message }: ErrorMessageProps) {
  return (
    <Alert color="danger" className="my-2">
      <i className="fa fa-close" /> {message}
    </Alert>
  );
}

export default ErrorMessage;
