// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useRef, useState } from "react";
import {
  Button,
  Col,
  Form,
  FormGroup,
  FormText,
  Input,
  InputGroup,
  InputGroupAddon,
  InputGroupText,
  Row,
} from "reactstrap";
import { Trans, useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import NumberInput from "react-number-format";
import SelectDropdown from "../select";
import { settingsContext } from "../../contexts/app";
import { FiatCurrency, Currency } from "../../interfaces/currencies";
import { DepositData } from "./interfaces";
import { Controller, useForm } from "react-hook-form";
import {
  fiatFromDiemFloat,
  fiatToDiemHumanFriendly,
  fiatToHumanFriendlyRate,
  normalizeDiemAmount,
} from "../../utils/amount-precision";
import {
  fiatCurrenciesOptions,
  currenciesWithBalanceOptions,
  paymentMethodOptions,
} from "../../utils/dropdown-options";

interface DepositFormProps {
  value: DepositData;
  onSubmit: (value: DepositData) => void;
}

function DepositForm({ value, onSubmit }: DepositFormProps) {
  const { t } = useTranslation("transfer");
  const [settings] = useContext(settingsContext)!;
  const { errors, handleSubmit, control, setValue, watch } = useForm<DepositData>();

  const [selectedCurrency, setSelectedCurrency] = useState<Currency | undefined>(value.currency);
  const [selectedFiatCurrency, setSelectedFiatCurrency] = useState<FiatCurrency>(
    value.fiatCurrency
  );
  const amount = watch("amount") || 0;
  const priceRef = useRef<HTMLInputElement>(null);

  const currency = selectedCurrency ? settings.currencies[selectedCurrency] : undefined;

  const fiatCurrency = selectedFiatCurrency
    ? settings.fiatCurrencies[selectedFiatCurrency]
    : undefined;

  const exchangeRate = currency ? currency.rates[selectedFiatCurrency] : 0;

  function calcPrice(amount: number) {
    return amount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  return (
    <>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <h3>{t("deposit.form.title")}</h3>
        <FormGroup>
          <FormText className="text-capitalize-first">{t("deposit.form.funding_source")}</FormText>
          <Controller
            invalid={!!errors.fundingSource}
            control={control}
            name="fundingSource"
            rules={{
              required: (
                <Trans
                  i18nKey="validations:required"
                  values={{ field: t("deposit.form.funding_source_placeholder") }}
                />
              ),
            }}
            defaultValue={value.fundingSource}
            as={
              <SelectDropdown
                label={t("deposit.form.funding_source_placeholder")}
                options={paymentMethodOptions(settings.paymentMethods || [])}
                dropdownAction={
                  <Button tag={Link} to="/settings" outline block color="black" size="sm">
                    {t("deposit.form.manage_payment_methods")}
                  </Button>
                }
              />
            }
          />
          {errors.fundingSource && (
            <FormText color="danger">{errors.fundingSource.message}</FormText>
          )}
        </FormGroup>
        <FormGroup>
          <FormText className="text-capitalize-first">{t("deposit.form.currency")}</FormText>
          <Controller
            invalid={!!errors.currency}
            control={control}
            name="currency"
            rules={{
              required: (
                <Trans
                  i18nKey="validations:required"
                  values={{ field: t("deposit.form.currency_placeholder") }}
                />
              ),
            }}
            defaultValue={value.currency}
            onChange={([val]) => {
              setSelectedCurrency(val);
              return val;
            }}
            as={
              <SelectDropdown
                label={t("deposit.form.currency_placeholder")}
                options={currenciesWithBalanceOptions(
                  settings.currencies,
                  settings.account!.balances
                )}
              />
            }
          />
          {errors.currency && <FormText color="danger">{errors.currency.message}</FormText>}
        </FormGroup>
        <Row>
          <Col sm="6">
            <FormGroup>
              <FormText className="text-capitalize-first">{t("deposit.form.amount")}</FormText>
              <InputGroup>
                <Controller
                  invalid={!!errors.amount}
                  control={control}
                  name="amount"
                  rules={{
                    required: (
                      <Trans
                        i18nKey="validations:required"
                        values={{ field: t("deposit.form.amount") }}
                      />
                    ),
                    min: {
                      value: 1,
                      message: (
                        <Trans
                          i18nKey="validations:min"
                          values={{ field: t("deposit.form.amount"), min: 1 }}
                        />
                      ),
                    },
                  }}
                  defaultValue={value.amount || 0}
                  onChange={([e]) => {
                    const value = parseFloat(e.target.value);
                    return isNaN(value) ? "" : normalizeDiemAmount(value);
                  }}
                  onClick={(e) => {
                    const value = parseFloat(e.target.value);
                    if (!value) {
                      setValue("amount", ("" as unknown) as number);
                    }
                  }}
                  onBlur={([e]) => {
                    const value = e.target.value;
                    if (!value.length) {
                      setValue("amount", 0);
                    }
                  }}
                  disabled={!selectedCurrency}
                  as={<Input min={0} step="any" type="number" />}
                />
                <InputGroupAddon addonType="append">
                  <InputGroupText>{currency?.sign}</InputGroupText>
                </InputGroupAddon>
              </InputGroup>
              {errors.amount && <FormText color="danger">{errors.amount.message}</FormText>}
            </FormGroup>
          </Col>
          <Col sm="6">
            <FormGroup>
              <FormText className="text-capitalize-first">{t("deposit.form.price")}</FormText>
              <InputGroup>
                <NumberInput
                  getInputRef={priceRef}
                  className="form-control"
                  prefix={fiatCurrency?.sign}
                  allowNegative={false}
                  allowEmptyFormatting={false}
                  thousandSeparator={true}
                  value={amount ? fiatToDiemHumanFriendly(calcPrice(amount)) : ""}
                  onValueChange={(values) => {
                    if (priceRef.current === document.activeElement) {
                      const newPrice = fiatFromDiemFloat(values.floatValue || 0);
                      const amount = normalizeDiemAmount(calcAmount(newPrice));
                      setValue("amount", amount);
                    }
                  }}
                  disabled={!selectedCurrency}
                />
                <Controller
                  invalid={!!errors.fiatCurrency}
                  control={control}
                  name="fiatCurrency"
                  rules={{
                    required: (
                      <Trans
                        i18nKey="validations:required"
                        values={{ field: t("deposit.form.fiatCurrency") }}
                      />
                    ),
                  }}
                  defaultValue={value.fiatCurrency}
                  onChange={([val]) => {
                    setSelectedFiatCurrency(val);
                    return val;
                  }}
                  as={
                    <SelectDropdown
                      addonType="append"
                      options={fiatCurrenciesOptions(settings.fiatCurrencies)}
                    />
                  }
                />
              </InputGroup>
              {errors.fiatCurrency && (
                <FormText color="danger">{errors.fiatCurrency.message}</FormText>
              )}
            </FormGroup>
          </Col>
        </Row>
        {currency && fiatCurrency && (
          <FormGroup>
            <FormText>{t("deposit.form.exchange_rate")}</FormText>
            <p className="text-black">
              1 {currency.sign} = {fiatToHumanFriendlyRate(exchangeRate)} {fiatCurrency.symbol}
            </p>
          </FormGroup>
        )}
        <Button color="black" type="submit" block>
          {t("deposit.form.review")}
        </Button>
      </Form>
    </>
  );
}

export default DepositForm;
