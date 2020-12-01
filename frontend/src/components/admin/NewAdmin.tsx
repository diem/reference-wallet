// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Trans, useTranslation } from "react-i18next";
import { Button, Form, FormGroup, FormText, Input, Modal, ModalBody } from "reactstrap";

import CloseButton from "../CloseButton";
import ErrorMessage from "../Messages/ErrorMessage";
import { useForm } from "react-hook-form";

export type NewAdminStatus = "editing" | "sending" | "failed" | "inactive";

interface NewAdminModalProps {
  status: NewAdminStatus;
  errorMessage?: string;
  onSubmit: (admin: AdminFormData) => void;
  onClose: () => void;
}

interface AdminFormData {
  firstName: string;
  lastName: string;
  username: string;
  password: string;
  passwordConfirmation: string;
}

export default function NewAdminModal({
  status,
  errorMessage,
  onSubmit,
  onClose,
}: NewAdminModalProps) {
  const { t } = useTranslation("admin");
  const { register, errors, handleSubmit, watch } = useForm<AdminFormData>();

  const password = watch("password");

  const passwordStrengthRegex = new RegExp("^(?=.*\\d)(?=.*[a-zA-Z]).{8,}$");

  return (
    <Modal className="modal-dialog-centered" isOpen={status !== "inactive"} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        {status === "failed" && errorMessage && <ErrorMessage message={errorMessage} />}

        <h3>{t("newAdmin.title")}</h3>

        <Form role="form" onSubmit={handleSubmit(onSubmit)}>
          <FormGroup className="mb-4">
            <Input
              innerRef={register({
                required: (
                  <Trans
                    i18nKey="validations:required"
                    values={{ field: t("fields.first_name") }}
                  />
                ),
                minLength: {
                  value: 2,
                  message: (
                    <Trans
                      i18nKey="validations:minLength"
                      values={{ field: t("fields.first_name"), min: 2 }}
                    />
                  ),
                },
              })}
              invalid={!!errors.firstName}
              placeholder={t("fields.first_name")}
              name="firstName"
              type="text"
            />
            {errors.firstName && <FormText color="danger">{errors.firstName.message}</FormText>}
          </FormGroup>

          <FormGroup className="mb-4">
            <Input
              invalid={!!errors.lastName}
              innerRef={register({
                required: (
                  <Trans i18nKey="validations:required" values={{ field: t("fields.last_name") }} />
                ),
                minLength: {
                  value: 2,
                  message: (
                    <Trans
                      i18nKey="validations:minLength"
                      values={{ field: t("fields.last_name"), min: 2 }}
                    />
                  ),
                },
              })}
              placeholder={t("fields.last_name")}
              name="lastName"
              type="text"
            />
            {errors.lastName && <FormText color="danger">{errors.lastName.message}</FormText>}
          </FormGroup>

          <FormGroup className="mb-4">
            <Input
              invalid={!!errors.username}
              innerRef={register({
                required: (
                  <Trans i18nKey="validations:required" values={{ field: t("fields.username") }} />
                ),
              })}
              placeholder={t("fields.username")}
              name="username"
              type={process.env.NODE_ENV === "production" ? "text" : "email"}
            />
            {errors.username && <FormText color="danger">{errors.username.message}</FormText>}
          </FormGroup>

          <FormGroup className="mb-4">
            <Input
              invalid={!!errors.password}
              innerRef={register({
                validate: (value) => {
                  if (!passwordStrengthRegex.test(value)) {
                    return (
                      <Trans
                        i18nKey="validations:pattern"
                        values={{ field: t("fields.password") }}
                      />
                    );
                  }
                },
              })}
              placeholder={t("fields.password")}
              name="password"
              type="password"
              autoComplete="off"
            />
            {errors.password && <FormText color="danger">{errors.password.message}</FormText>}
          </FormGroup>
          {!!password?.length && (
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
              invalid={!!errors.passwordConfirmation}
              innerRef={register({
                validate: (value) => {
                  if (value !== password) {
                    return <Trans i18nKey="validations:passwordsDontMatch" />;
                  }
                },
              })}
              placeholder={t("fields.confirm_password")}
              name="passwordConfirmation"
              type="password"
              autoComplete="off"
            />
            {errors.passwordConfirmation && (
              <FormText color="danger">{errors.passwordConfirmation.message}</FormText>
            )}
          </FormGroup>

          {status === "sending" && (
            <Button color="black" type="button" block disabled>
              <i className="fa fa-spin fa-spinner" />
            </Button>
          )}
          {status !== "sending" && (
            <Button color="black" type="submit" block>
              {t("newAdmin.submit")}
            </Button>
          )}
        </Form>
      </ModalBody>
    </Modal>
  );
}
