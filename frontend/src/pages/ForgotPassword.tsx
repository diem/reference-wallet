// Copyright (c) The Diem Core Contributors
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
  const [username, setUsername] = useState<string>("");
  const [passwordResetToken, setPasswordResetToken] = useState<string | undefined>();

  const onFormSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const token = await new BackendClient().forgotPassword(username);
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
            <InfoMessage
              message={
                process.env.NODE_ENV === "production"
                  ? t("forgot_password.success_username", { replace: { username } })
                  : t("forgot_password.success_email", { replace: { email: username } })
              }
            />
          )}

          {submitStatus !== "success" && (
            <>
              <p>
                {process.env.NODE_ENV === "production" ? (
                  <Trans
                    t={t}
                    i18nKey="forgot_password.text_username"
                    components={[
                      <Link to="/signup">sign up</Link>,
                      <Link to="/login">login here</Link>,
                    ]}
                  />
                ) : (
                  <Trans
                    t={t}
                    i18nKey="forgot_password.text_email"
                    components={[
                      <Link to="/signup">sign up</Link>,
                      <Link to="/login">login here</Link>,
                    ]}
                  />
                )}
              </p>

              <Form role="form" onSubmit={onFormSubmit}>
                <FormGroup className="mb-4">
                  <Input
                    placeholder={
                      process.env.NODE_ENV === "production"
                        ? t("fields.username")
                        : t("fields.email")
                    }
                    type={process.env.NODE_ENV === "production" ? "text" : "email"}
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
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
