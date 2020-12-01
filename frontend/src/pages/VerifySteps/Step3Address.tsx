// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Button, Col, Form, FormGroup, FormText, Input, Row } from "reactstrap";
import { useForm } from "react-hook-form";
import { UserInfo } from "../../interfaces/user";
import { AddressInfo } from "./interfaces";

interface Step3AddressProps {
  info: UserInfo;
  onBack: () => void;
  onSubmit: (info: UserInfo) => void;
}

const Step3Address = ({ info, onBack, onSubmit }: Step3AddressProps) => {
  const { t } = useTranslation("verify");
  const { register, errors, handleSubmit, setValue } = useForm<AddressInfo>();

  useEffect(() => {
    setValue("address_1", info.address_1);
    setValue("address_2", info.address_2);
    setValue("city", info.city);
    setValue("state", info.state);
    setValue("zip", info.zip);
  }, [info]);

  function onFormSubmit({ address_1, address_2, city, state, zip }: AddressInfo) {
    onSubmit({ ...info, address_1, address_2, city, state, zip });
  }

  return (
    <>
      <h1 className="h3">{t("step3.title")}</h1>
      <p>{t("step3.description")}</p>

      <Form role="form" onSubmit={handleSubmit(onFormSubmit)}>
        <FormGroup className="mb-4">
          <Input
            invalid={!!errors.address_1}
            innerRef={register({
              required: (
                <Trans
                  i18nKey="validations:required"
                  values={{ field: t("step3.fields.address_1") }}
                />
              ),
            })}
            placeholder={t("step3.fields.address_1")}
            name="address_1"
            type="text"
            disabled={process.env.NODE_ENV === "production"}
            defaultValue={info.address_1}
          />
          {errors.address_1 && <FormText color="danger">{errors.address_1.message}</FormText>}
        </FormGroup>

        <FormGroup className="mb-4">
          <Input
            invalid={!!errors.address_2}
            innerRef={register}
            placeholder={t("step3.fields.address_2")}
            name="address_2"
            type="text"
            disabled={process.env.NODE_ENV === "production"}
            defaultValue={info.address_2}
          />
          {errors.address_2 && <FormText color="danger">{errors.address_2.message}</FormText>}
        </FormGroup>

        <FormGroup className="mb-4">
          <Input
            invalid={!!errors.city}
            innerRef={register({
              required: (
                <Trans i18nKey="validations:required" values={{ field: t("step3.fields.city") }} />
              ),
            })}
            placeholder={t("step3.fields.city")}
            name="city"
            type="text"
            disabled={process.env.NODE_ENV === "production"}
            defaultValue={info.city}
          />
          {errors.city && <FormText color="danger">{errors.city.message}</FormText>}
        </FormGroup>

        <FormGroup className="mb-4">
          <Input
            invalid={!!errors.state}
            innerRef={register}
            placeholder={t("step3.fields.state")}
            name="state"
            type="text"
            disabled={process.env.NODE_ENV === "production"}
            defaultValue={info.state}
          />
          {errors.state && <FormText color="danger">{errors.state.message}</FormText>}
        </FormGroup>

        <FormGroup className="mb-4">
          <Input
            invalid={!!errors.zip}
            innerRef={register}
            placeholder={t("step3.fields.zip")}
            name="zip"
            type="text"
            disabled={process.env.NODE_ENV === "production"}
            defaultValue={info.zip}
          />
          {errors.zip && <FormText color="danger">{errors.zip.message}</FormText>}
        </FormGroup>

        <Row>
          <Col>
            <Button outline color="black" block onClick={onBack}>
              {t("step3.back")}
            </Button>
          </Col>
          <Col>
            <Button color="black" type="submit" block>
              {t("step3.continue")}
            </Button>
          </Col>
        </Row>
      </Form>
    </>
  );
};

export default Step3Address;
