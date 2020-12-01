// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Button, Col, Form, FormGroup, FormText, Row } from "reactstrap";
import { Controller, useForm } from "react-hook-form";
import { countries } from "countries-list";
import { UserInfo } from "../../interfaces/user";
import SelectDropdown from "../../components/select";
import { CountryInfo } from "./interfaces";

export const countriesList = Object.keys(countries)
  .sort((a, b) => {
    const countryA = countries[a];
    const countryB = countries[b];
    return countryA.name.localeCompare(countryB.name);
  })
  .reduce((list, code) => {
    const country = countries[code];
    list[code] = `${country.emoji} ${country.name} (${country.native})`;
    return list;
  }, {});

interface Step2CountryProps {
  info: UserInfo;
  onSubmit: (info: UserInfo) => void;
  onBack: () => void;
}

const Step2Country = ({ info, onBack, onSubmit }: Step2CountryProps) => {
  const { t } = useTranslation("verify");
  const { errors, handleSubmit, control, setValue } = useForm<CountryInfo>();

  useEffect(() => {
    setValue("country", info.country!);
  }, [info]);

  function onFormSubmit({ country }: CountryInfo) {
    onSubmit({ ...info, country });
  }

  return (
    <>
      <h1 className="h3">{t("step2.title")}</h1>
      <p>{t("step2.description")}</p>

      <Form role="form" onSubmit={handleSubmit(onFormSubmit)}>
        <FormGroup className="mb-4">
          <Controller
            invalid={!!errors.country}
            control={control}
            name="country"
            rules={{
              required: (
                <Trans
                  i18nKey="validations:required"
                  values={{ field: t("step2.fields.country") }}
                />
              ),
            }}
            disabled={process.env.NODE_ENV === "production"}
            defaultValue={info.country}
            as={<SelectDropdown label={t("step2.fields.country")} options={countriesList} />}
          />
          {errors.country && <FormText color="danger">{errors.country.message}</FormText>}
        </FormGroup>
        <Row>
          <Col>
            <Button outline color="black" block onClick={onBack}>
              {t("step2.back")}
            </Button>
          </Col>
          <Col>
            <Button color="black" type="submit" block>
              {t("step2.continue")}
            </Button>
          </Col>
        </Row>
      </Form>
    </>
  );
};

export default Step2Country;
