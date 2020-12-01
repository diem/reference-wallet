// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { Alert } from "reactstrap";
import React from "react";

interface SuccessMessageProps {
  message: string;
}

function SuccessMessage({ message }: SuccessMessageProps) {
  return (
    <Alert color="success" className="my-2">
      <i className="fa fa-check" /> {message}
    </Alert>
  );
}

export default SuccessMessage;
