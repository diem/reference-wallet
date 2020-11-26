// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "reactstrap";

function VerifyingMessage() {
  const { t } = useTranslation("layout");

  return (
    <section className="slim-section m-auto">
      <h1 className="h3">{t("verification_pending.title")}</h1>
      <p>{t("verification_pending.description")}</p>
      <div className="d-flex flex-column align-items-center mt-4">
        <Spinner type="grow" color="primary" />
        {t("verification_pending.redirect")}
      </div>
    </section>
  );
}

export default VerifyingMessage;
