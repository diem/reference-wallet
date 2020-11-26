// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Button, Col, Form, FormGroup, FormText, Row } from "reactstrap";
import { settingsContext } from "../../contexts/app";
import SelectDropdown from "../../components/select";
import { FiatCurrency } from "../../interfaces/currencies";
import { Controller, useForm } from "react-hook-form";
import { UserInfo } from "../../interfaces/user";
import { DefaultSettings } from "./interfaces";

interface StepDefaultCurrencyProps {
  info: UserInfo;
  onBack: () => void;
  onContinue: (info: UserInfo) => void;
}

const Step5DefaultCurrency = ({ info, onContinue, onBack }: StepDefaultCurrencyProps) => {
  const { t } = useTranslation("verify");
  const [settings] = useContext(settingsContext)!;
  const { errors, handleSubmit, control } = useForm<DefaultSettings>();

  function onFormSubmit({ default_fiat_currency }: DefaultSettings) {
    onContinue({ ...info, selected_fiat_currency: default_fiat_currency });
  }

  const fiatCurrencies: { [key in FiatCurrency]?: string } = Object.keys(
    settings.fiatCurrencies
  ).reduce((currencies, fiat) => {
    const currency = settings.fiatCurrencies[fiat];
    currencies[fiat] = `${currency.sign} ${currency.symbol}`;
    return currencies;
  }, {});

  return (
    <>
      <h1 className="h3">{t("step5.title")}</h1>
      <p>{t("step5.description")}</p>

      <Form role="form" onSubmit={handleSubmit(onFormSubmit)}>
        <FormGroup className="mb-4">
          <Controller
            control={control}
            name="default_fiat_currency"
            rules={{
              required: <Trans i18nKey="validations:required" />,
            }}
            defaultValue="USD"
            as={<SelectDropdown label={t("step5.fields.fiat_currency")} options={fiatCurrencies} />}
          />
          {errors.default_fiat_currency && (
            <FormText color="danger">{errors.default_fiat_currency.message}</FormText>
          )}
        </FormGroup>
        <Row>
          <Col>
            <Button outline color="black" block onClick={onBack}>
              {t("step5.back")}
            </Button>
          </Col>
          <Col>
            <Button color="black" type="submit" block>
              {t("step5.continue")}
            </Button>
          </Col>
        </Row>
      </Form>
    </>
  );
};

export default Step5DefaultCurrency;
