// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { FormEvent, useState } from "react";
import { Button, Container, Form, FormGroup, Input } from "reactstrap";
import { Trans, useTranslation } from "react-i18next";
import { Link, Redirect } from "react-router-dom";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import InfoMessage from "../components/Messages/InfoMessage";
import ErrorMessage from "../components/Messages/ErrorMessage";

function ForgotPassword() {
  const { t } = useTranslation("auth");

  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");
  const [email, setEmail] = useState<string>("");
  const [passwordResetToken, setPasswordResetToken] = useState<string | undefined>();

  const onFormSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const token = await new BackendClient().forgotPassword(email);
      setSubmitStatus("success");

      setTimeout(() => {
        setPasswordResetToken(token);
      }, 3000);
    } catch (e) {
      setSubmitStatus("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  };

  return (
    <>
      {passwordResetToken && <Redirect to={`/reset-password?token=${passwordResetToken}`} />}
      <Container className="py-5 d-flex flex-column">
        <section className="slim-section m-auto">
          <h1 className="h3">{t("forgot_password.headline")}</h1>

          {errorMessage && <ErrorMessage message={errorMessage} />}
          {submitStatus === "success" && (
            <InfoMessage message={t("forgot_password.success", { replace: { email } })} />
          )}

          {submitStatus !== "success" && (
            <>
              <p>
                <Trans
                  t={t}
                  i18nKey="forgot_password.text"
                  components={[
                    <Link to="/signup">sign up</Link>,
                    <Link to="/login">login here</Link>,
                  ]}
                />
              </p>

              <Form role="form" onSubmit={onFormSubmit}>
                <FormGroup className="mb-4">
                  <Input
                    placeholder={t("fields.email")}
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </FormGroup>
                {submitStatus === "sending" && (
                  <Button color="black" type="button" block disabled>
                    <i className="fa fa-spin fa-spinner" />
                  </Button>
                )}
                {submitStatus !== "sending" && (
                  <Button color="black" type="submit" block>
                    {t("forgot_password.submit")}
                  </Button>
                )}
              </Form>
            </>
          )}
        </section>
      </Container>
    </>
  );
}

export default ForgotPassword;
