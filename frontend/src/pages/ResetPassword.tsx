// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { FormEvent, useState } from "react";
import { Button, Container, Form, FormGroup, FormText, Input } from "reactstrap";
import { Redirect } from "react-router-dom";
import { useTranslation } from "react-i18next";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import ErrorMessage from "../components/Messages/ErrorMessage";

function ResetPassword() {
  const { t } = useTranslation("auth");

  const queryParams = new URLSearchParams(window.location.search);
  const token = queryParams.get("token");

  const [errorMessage, setErrorMessage] = useState<string | undefined>(
    !token ? t("reset_password.missing_token") : undefined
  );
  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const passwordStrengthRegex = new RegExp("^(?=.*\\d)(?=.*[a-zA-Z]).{8,}$");

  const onFormSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!passwordStrengthRegex.test(password)) {
      return setErrorMessage(t("fields.password_strength.error"));
    }
    if (!token) {
      return setErrorMessage(t("reset_password.missing_token"));
    }
    if (password !== passwordConfirmation) {
      return setErrorMessage(t("reset_password.password_mismatch"));
    }

    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      await new BackendClient().resetUserPassword(token!, password);
      setSubmitStatus("success");
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
      {submitStatus === "success" && <Redirect to="/" />}
      <Container className="py-5 d-flex flex-column">
        <section className="slim-section m-auto">
          {errorMessage && <ErrorMessage message={errorMessage} />}

          {token && (
            <>
              <h1 className="h3">{t("reset_password.headline")}</h1>
              <p>{t("reset_password.text")}</p>

              <Form role="form" onSubmit={onFormSubmit}>
                <FormGroup className="mb-4">
                  <Input
                    placeholder={t("fields.new_password")}
                    type="password"
                    autoComplete="off"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </FormGroup>
                {!!password.length && (
                  <FormText className="mb-4">
                    <strong>{t("fields.password_strength.title")}:</strong>{" "}
                    {passwordStrengthRegex.test(password) ? (
                      <span className="text-success">{t("fields.password_strength.strong")}</span>
                    ) : (
                      <span className="text-danger">{t("fields.password_strength.weak")}</span>
                    )}
                    <div>{t("fields.password_strength.text")}</div>
                  </FormText>
                )}
                <FormGroup className="mb-4">
                  <Input
                    placeholder={t("fields.confirm_password")}
                    type="password"
                    autoComplete="off"
                    required
                    value={passwordConfirmation}
                    onChange={(e) => setPasswordConfirmation(e.target.value)}
                  />
                </FormGroup>
                {submitStatus === "sending" && (
                  <Button color="black" type="button" block disabled>
                    <i className="fa fa-spin fa-spinner" />
                  </Button>
                )}
                {submitStatus !== "sending" && (
                  <Button color="black" type="submit" block>
                    {t("reset_password.submit")}
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

export default ResetPassword;
