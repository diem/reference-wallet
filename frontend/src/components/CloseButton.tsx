// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";

interface CloseButtonProps {
  onClick: () => void;
}

function CloseButton({ onClick }: CloseButtonProps) {
  const { t } = useTranslation("layout");

  return (
    <button
      aria-label={t("close")}
      className="close"
      data-dismiss="modal"
      type="button"
      onClick={onClick}
    >
      <img src={require("assets/img/close.svg")} alt="Close" />
    </button>
  );
}

export default CloseButton;
