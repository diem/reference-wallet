// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "reactstrap";

function SignedUpMessage({ username }: { username: string }) {
  const { t } = useTranslation("auth");

  return (
    <>
      {process.env.NODE_ENV === "production" ? (
        <>
          <h1 className="h3">{t("signup.success_username.headline")}</h1>
          <p>{t("signup.success_username.text", { replace: { email: username } })}</p>
        </>
      ) : (
        <>
          <h1 className="h3">{t("signup.success_email.headline")}</h1>
          <p>{t("signup.success_email.text", { replace: { username } })}</p>
        </>
      )}
      <div className="d-flex flex-column align-items-center mt-4">
        <Spinner type="grow" color="primary" />
        {t("signup.redirect", { replace: { username } })}
      </div>
    </>
  );
}

export default SignedUpMessage;
