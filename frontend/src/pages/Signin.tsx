// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import * as React from "react";
import { FormEvent, useState } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Button, Container, Form, FormGroup, Input } from "reactstrap";
import { Link, Redirect } from "react-router-dom";
import SessionStorage from "../services/sessionStorage";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import ErrorMessage from "../components/Messages/ErrorMessage";

function Signin() {
  const { t } = useTranslation("auth");

  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const backendClient = new BackendClient();

  const onFormSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const authToken = await backendClient.signinUser(username, password);
      SessionStorage.storeAccessToken(authToken);
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

          <h1 className="h3">{t("signin.headline")}</h1>
          <p>
            <Trans t={t} i18nKey="signin.text" values={{ name: t("layout:name") }}>
              <Link to="/signup">Sign up here</Link>.
            </Trans>
          </p>

          <Form role="form" onSubmit={onFormSubmit}>
            <FormGroup className="mb-4">
              <Input
                placeholder={
                  process.env.NODE_ENV === "production" ? t("fields.username") : t("fields.email")
                }
                type={process.env.NODE_ENV === "production" ? "text" : "email"}
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </FormGroup>
            <FormGroup className="mb-4">
              <Input
                placeholder={t("fields.password")}
                type="password"
                autoComplete="off"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <div className="mt-2 small">
                <Link to="forgot-password" className="text-muted">
                  {t("signin.links.forgot_password")}
                </Link>
              </div>
            </FormGroup>

            {submitStatus === "sending" && (
              <Button block color="black" type="button" disabled>
                <i className="fa fa-spin fa-spinner" />
              </Button>
            )}
            {submitStatus !== "sending" && (
              <Button block color="black" type="submit">
                {t("signin.submit")}
              </Button>
            )}
          </Form>
        </section>
      </Container>
    </>
  );
}

export default Signin;
