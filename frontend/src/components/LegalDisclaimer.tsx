// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";

function LegalDisclaimer() {
  const { t } = useTranslation("legal");

  return (
    <div className="container py-4 justify-content-center align-items-center d-flex flex-column h-100">
      {t("legal_disclaimer")}

      <i className="fa fa-spin fa-spinner h2 my-4" />
    </div>
  );
}

export default LegalDisclaimer;
