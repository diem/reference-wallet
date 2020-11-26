// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
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
import SelectDropdown from "../select";
import { Currency } from "../../interfaces/currencies";
import { settingsContext } from "../../contexts/app";
import { ConvertData } from "./interfaces";
import {
  diemAmountFromFloat,
  diemAmountToHumanFriendly,
  normalizeDiemAmount,
} from "../../utils/amount-precision";
import { currenciesWithBalanceOptions } from "../../utils/dropdown-options";

interface ConvertFormProps {
  value: ConvertData;
  onSubmit: (data: ConvertData) => void;
}

function ConvertForm({ value, onSubmit }: ConvertFormProps) {
  const { t } = useTranslation("transfer");
  const [settings] = useContext(settingsContext)!;
  const { errors, handleSubmit, control, setValue, watch } = useForm<ConvertData>();

  const [selectedFromCurrency, setSelectedFromCurrency] = useState<Currency | undefined>(
    value.fromCurrency
  );
  const [selectedToCurrency, setSelectedToCurrency] = useState<Currency | undefined>(
    value.toCurrency
  );
  const amount = watch("amount") || 0;
  const priceRef = useRef<HTMLInputElement>(null);

  const fromCurrency = selectedFromCurrency ? settings.currencies[selectedFromCurrency] : undefined;
  const toCurrency = selectedToCurrency ? settings.currencies[selectedToCurrency] : undefined;

  const exchangeRate =
    fromCurrency && selectedToCurrency && selectedFromCurrency !== selectedToCurrency
      ? fromCurrency.rates[selectedToCurrency]
      : 0;

  function calcPrice(amount: number) {
    return amount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  return (
    <Form onSubmit={handleSubmit(onSubmit)}>
      <h3>{t("convert.form.title")}</h3>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("convert.form.currency_from")}</FormText>
        <Controller
          invalid={!!errors.fromCurrency}
          control={control}
          name="fromCurrency"
          rules={{
            required: (
              <Trans
                i18nKey="validations:required"
                values={{ field: t("convert.form.currency_placeholder") }}
              />
            ),
          }}
          defaultValue={value.fromCurrency}
          onChange={([val]) => {
            setSelectedFromCurrency(val);
            return val;
          }}
          as={
            <SelectDropdown
              label={t("convert.form.currency_placeholder")}
              options={currenciesWithBalanceOptions(
                settings.currencies,
                settings.account!.balances
              )}
            />
          }
        />
        {errors.fromCurrency && <FormText color="danger">{errors.fromCurrency.message}</FormText>}
      </FormGroup>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("convert.form.currency_to")}</FormText>
        <Controller
          invalid={!!errors.toCurrency}
          control={control}
          name="toCurrency"
          rules={{
            required: (
              <Trans
                i18nKey="validations:required"
                values={{ field: t("convert.form.currency_placeholder") }}
              />
            ),
            validate: (selectedCurrency) => {
              const fromCurrency = watch("fromCurrency");
              const currenciesEqual = selectedCurrency === fromCurrency;
              if (currenciesEqual) {
                return t("validations:noEqualCurrencies")!;
              }
              return true;
            },
          }}
          defaultValue={value.toCurrency}
          onChange={([val]) => {
            setSelectedToCurrency(val);
            return val;
          }}
          as={
            <SelectDropdown
              label={t("convert.form.currency_placeholder")}
              options={currenciesWithBalanceOptions(
                settings.currencies,
                settings.account!.balances
              )}
            />
          }
        />
        {errors.toCurrency && <FormText color="danger">{errors.toCurrency.message}</FormText>}
      </FormGroup>
      <Row>
        <Col sm="6">
          <FormGroup>
            <FormText className="text-capitalize-first">{t("convert.form.amount")}</FormText>
            <InputGroup>
              <Controller
                invalid={!!errors.amount}
                control={control}
                name="amount"
                rules={{
                  required: (
                    <Trans
                      i18nKey="validations:required"
                      values={{ field: t("convert.form.amount") }}
                    />
                  ),
                  min: {
                    value: 1,
                    message: (
                      <Trans
                        i18nKey="validations:min"
                        values={{ field: t("convert.form.amount"), min: 1 }}
                      />
                    ),
                  },
                  validate: (enteredAmount: number) => {
                    const selectedFromCurrency = watch("fromCurrency");

                    if (selectedFromCurrency) {
                      const selectedCurrencyBalance = settings.account!.balances.find(
                        (balance) => balance.currency === selectedFromCurrency
                      )!;
                      if (diemAmountFromFloat(enteredAmount) > selectedCurrencyBalance.balance) {
                        return t("validations:noMoreThanBalance", {
                          replace: {
                            field: t("convert.form.amount"),
                            currency: selectedCurrencyBalance.currency,
                          },
                        })!;
                      }
                    }
                    return true;
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
                disabled={!selectedFromCurrency || !selectedToCurrency}
                as={<Input min={0} step="any" type="number" />}
              />
              <InputGroupAddon addonType="append">
                <InputGroupText>{fromCurrency?.sign}</InputGroupText>
              </InputGroupAddon>
            </InputGroup>
            {errors.amount && <FormText color="danger">{errors.amount.message}</FormText>}
          </FormGroup>
        </Col>
        <Col sm="6">
          <FormGroup>
            <FormText className="text-capitalize-first">{t("convert.form.price")}</FormText>
            <InputGroup>
              <Input
                innerRef={priceRef}
                min={0}
                step="any"
                type="number"
                value={amount ? diemAmountToHumanFriendly(calcPrice(amount)) : ""}
                onChange={(e) => {
                  if (e.target === document.activeElement) {
                    const value = parseFloat(e.target.value);
                    const newPrice = diemAmountFromFloat(value || 0);
                    const amount = normalizeDiemAmount(calcAmount(newPrice));
                    setValue("amount", amount);
                  }
                }}
                disabled={!selectedFromCurrency || !selectedToCurrency}
              />
              <InputGroupAddon addonType="append">
                <InputGroupText>{toCurrency?.sign}</InputGroupText>
              </InputGroupAddon>
            </InputGroup>
          </FormGroup>
        </Col>
      </Row>
      {fromCurrency && toCurrency && fromCurrency !== toCurrency && (
        <FormGroup>
          <FormText>{t("convert.form.exchange_rate")}</FormText>
          <p className="text-black">
            1 {fromCurrency.sign} = {diemAmountToHumanFriendly(exchangeRate)} {toCurrency.sign}
          </p>
        </FormGroup>
      )}
      <Button color="black" type="submit" block>
        {t("convert.form.review")}
      </Button>
    </Form>
  );
}

export default ConvertForm;
