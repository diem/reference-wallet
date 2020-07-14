// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Alert } from "reactstrap";

interface InfoMessageProps {
  message: string;
}

function InfoMessage({ message }: InfoMessageProps) {
  return (
    <Alert color="info" className="my-2 small">
      <i className="fa fa-info-circle" /> {message}
    </Alert>
  );
}

export default InfoMessage;
