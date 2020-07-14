// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect } from "react";
import { Trans, useTranslation } from "react-i18next";
import { Button, Form, FormGroup, FormText, Input, InputGroup } from "reactstrap";
import { Controller, useForm } from "react-hook-form";
import { countries } from "countries-list";
import moment from "moment";
import { UserInfo } from "../../interfaces/user";
import SelectDropdown from "../../components/select";
import DateTimePicker from "../../components/datetime-picker";
import { IdentityInfo } from "./interfaces";

const phonePrefixes = Object.keys(countries).reduce((list, code) => {
  const country = countries[code];
  const phone = country.phone.split(",")[0];
  list[phone] = `+${phone} ${country.emoji}`;
  return list;
}, {});

interface Step1IdentityProps {
  info: UserInfo;
  onSubmit: (info: UserInfo) => void;
}

const Step1Identity = ({ info, onSubmit }: Step1IdentityProps) => {
  const { t } = useTranslation("verify");
  const { register, errors, handleSubmit, getValues, setValue, control } = useForm<IdentityInfo>();

  const [phonePrefix, phoneNumber] = info.phone.split(" ");

  useEffect(() => {
    const { first_name, last_name } = getValues();

    setValue("first_name", first_name.length ? first_name : info.first_name);
    setValue("last_name", last_name.length ? last_name : info.last_name);
    setValue("dob", info.dob);
    setValue("phone_prefix", phonePrefix);
    setValue("phone_number", phoneNumber);
  }, [info]);

  function onFormSubmit({ first_name, last_name, dob, phone_number, phone_prefix }: IdentityInfo) {
    onSubmit({ ...info, first_name, last_name, dob, phone: `${phone_prefix} ${phone_number}` });
  }

  return (
    <>
      <h1 className="h3">{t("step1.title")}</h1>
      <p>{t("step1.description")}</p>

      <Form role="form" onSubmit={handleSubmit(onFormSubmit)}>
        <FormGroup className="mb-4">
          <Input
            innerRef={register({
              required: (
                <Trans
                  i18nKey="validations:required"
                  values={{ field: t("step1.fields.first_name") }}
                />
              ),
              minLength: {
                value: 2,
                message: (
                  <Trans
                    i18nKey="validations:minLength"
                    values={{ field: t("step1.fields.first_name"), min: 2 }}
                  />
                ),
              },
            })}
            invalid={!!errors.first_name}
            placeholder={t("step1.fields.first_name")}
            name="first_name"
            type="text"
            defaultValue={info.first_name}
          />
          {errors.first_name && <FormText color="danger">{errors.first_name.message}</FormText>}
        </FormGroup>
        <FormGroup className="mb-4">
          <Input
            invalid={!!errors.last_name}
            innerRef={register({
              required: (
                <Trans
                  i18nKey="validations:required"
                  values={{ field: t("step1.fields.last_name") }}
                />
              ),
              minLength: {
                value: 2,
                message: (
                  <Trans
                    i18nKey="validations:minLength"
                    values={{ field: t("step1.fields.last_name"), min: 2 }}
                  />
                ),
              },
            })}
            placeholder={t("step1.fields.last_name")}
            name="last_name"
            type="text"
            defaultValue={info.last_name}
          />
          {errors.last_name && <FormText color="danger">{errors.last_name.message}</FormText>}
        </FormGroup>
        <FormGroup className="mb-4">
          <Controller
            invalid={!!errors.dob}
            control={control}
            name="dob"
            rules={{
              required: (
                <Trans i18nKey="validations:required" values={{ field: t("step1.fields.dob") }} />
              ),
              validate: (selectedDate) => {
                const date = moment.isMoment(selectedDate) ? selectedDate : moment(selectedDate);
                if (!date.isValid()) {
                  return t("validations:validDate")!;
                }
                if (date.isAfter()) {
                  return t("validations:pastDateOnly")!;
                }
                return true;
              },
            }}
            defaultValue={info.dob}
            as={
              <DateTimePicker
                placeholder={t("step1.fields.dob")}
                isValidDate={(currentDate) => currentDate.isBefore()}
              />
            }
          />
          {errors.dob && <FormText color="danger">{errors.dob.message}</FormText>}
        </FormGroup>
        <FormGroup className="mb-4">
          <InputGroup>
            <Controller
              invalid={!!errors.phone_prefix}
              control={control}
              name="phone_prefix"
              rules={{
                required: (
                  <Trans
                    i18nKey="validations:required"
                    values={{ field: t("step1.fields.phone_prefix") }}
                  />
                ),
              }}
              defaultValue={phonePrefix}
              as={<SelectDropdown addonType="prepend" options={phonePrefixes} />}
            />
            <Input
              invalid={!!errors.phone_number}
              name="phone_number"
              innerRef={register({
                required: (
                  <Trans
                    i18nKey="validations:required"
                    values={{ field: t("step1.fields.phone_number") }}
                  />
                ),
                pattern: {
                  value: new RegExp("^[0-9-s()]*$"),
                  message: (
                    <Trans
                      i18nKey="validations:numbersOnly"
                      values={{ field: t("step1.fields.phone_number") }}
                    />
                  ),
                },
              })}
              placeholder={t("step1.fields.phone_number")}
              type="tel"
              defaultValue={phoneNumber}
            />
          </InputGroup>
          {errors.phone_prefix && <FormText color="danger">{errors.phone_prefix.message}</FormText>}
          {errors.phone_number && <FormText color="danger">{errors.phone_number.message}</FormText>}
        </FormGroup>
        <Button color="black" type="submit" block>
          {t("step1.continue")}
        </Button>
      </Form>
    </>
  );
};

export default Step1Identity;
