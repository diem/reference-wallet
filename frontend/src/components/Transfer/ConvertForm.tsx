// Copyright (c) The Libra Core Contributors
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
import { LibraCurrency } from "../../interfaces/currencies";
import { settingsContext } from "../../contexts/app";
import { ConvertData } from "./interfaces";
import { libraFromFloat, libraToHumanFriendly, normalizeLibra } from "../../utils/amount-precision";
import { libraCurrenciesWithBalanceOptions } from "../../utils/dropdown-options";

interface ConvertFormProps {
  value: ConvertData;
  onSubmit: (data: ConvertData) => void;
}

function ConvertForm({ value, onSubmit }: ConvertFormProps) {
  const { t } = useTranslation("transfer");
  const [settings] = useContext(settingsContext)!;
  const { errors, handleSubmit, control, setValue, watch } = useForm<ConvertData>();

  const [selectedFromCurrency, setSelectedFromCurrency] = useState<LibraCurrency | undefined>(
    value.fromLibraCurrency
  );
  const [selectedToCurrency, setSelectedToCurrency] = useState<LibraCurrency | undefined>(
    value.toLibraCurrency
  );
  const libraAmount = watch("libraAmount") || 0;
  const priceRef = useRef<HTMLInputElement>(null);

  const fromCurrency = selectedFromCurrency ? settings.currencies[selectedFromCurrency] : undefined;
  const toCurrency = selectedToCurrency ? settings.currencies[selectedToCurrency] : undefined;

  const exchangeRate =
    fromCurrency && selectedToCurrency && selectedFromCurrency !== selectedToCurrency
      ? fromCurrency.rates[selectedToCurrency]
      : 0;

  function calcPrice(libraAmount: number) {
    return libraAmount * exchangeRate;
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
          invalid={!!errors.fromLibraCurrency}
          control={control}
          name="fromLibraCurrency"
          rules={{
            required: (
              <Trans
                i18nKey="validations:required"
                values={{ field: t("convert.form.currency_placeholder") }}
              />
            ),
          }}
          defaultValue={value.fromLibraCurrency}
          onChange={([val]) => {
            setSelectedFromCurrency(val);
            return val;
          }}
          as={
            <SelectDropdown
              label={t("convert.form.currency_placeholder")}
              options={libraCurrenciesWithBalanceOptions(
                settings.currencies,
                settings.account!.balances
              )}
            />
          }
        />
        {errors.fromLibraCurrency && (
          <FormText color="danger">{errors.fromLibraCurrency.message}</FormText>
        )}
      </FormGroup>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("convert.form.currency_to")}</FormText>
        <Controller
          invalid={!!errors.toLibraCurrency}
          control={control}
          name="toLibraCurrency"
          rules={{
            required: (
              <Trans
                i18nKey="validations:required"
                values={{ field: t("convert.form.currency_placeholder") }}
              />
            ),
            validate: (selectedCurrency) => {
              const fromLibraCurrency = watch("fromLibraCurrency");
              const currenciesEqual = selectedCurrency === fromLibraCurrency;
              if (currenciesEqual) {
                return t("validations:noEqualCurrencies")!;
              }
              return true;
            },
          }}
          defaultValue={value.toLibraCurrency}
          onChange={([val]) => {
            setSelectedToCurrency(val);
            return val;
          }}
          as={
            <SelectDropdown
              label={t("convert.form.currency_placeholder")}
              options={libraCurrenciesWithBalanceOptions(
                settings.currencies,
                settings.account!.balances
              )}
            />
          }
        />
        {errors.toLibraCurrency && (
          <FormText color="danger">{errors.toLibraCurrency.message}</FormText>
        )}
      </FormGroup>
      <Row>
        <Col sm="6">
          <FormGroup>
            <FormText className="text-capitalize-first">{t("convert.form.amount")}</FormText>
            <InputGroup>
              <Controller
                invalid={!!errors.libraAmount}
                control={control}
                name="libraAmount"
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
                    const selectedFromLibraCurrency = watch("fromLibraCurrency");

                    if (selectedFromLibraCurrency) {
                      const selectedCurrencyBalance = settings.account!.balances.find(
                        (balance) => balance.currency === selectedFromLibraCurrency
                      )!;
                      if (libraFromFloat(enteredAmount) > selectedCurrencyBalance.balance) {
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
                defaultValue={value.libraAmount || 0}
                onChange={([e]) => {
                  const value = parseFloat(e.target.value);
                  return isNaN(value) ? "" : normalizeLibra(value);
                }}
                onClick={(e) => {
                  const value = parseFloat(e.target.value);
                  if (!value) {
                    setValue("libraAmount", ("" as unknown) as number);
                  }
                }}
                onBlur={([e]) => {
                  const value = e.target.value;
                  if (!value.length) {
                    setValue("libraAmount", 0);
                  }
                }}
                disabled={!selectedFromCurrency || !selectedToCurrency}
                as={<Input min={0} step="any" type="number" />}
              />
              <InputGroupAddon addonType="append">
                <InputGroupText>{fromCurrency?.sign}</InputGroupText>
              </InputGroupAddon>
            </InputGroup>
            {errors.libraAmount && <FormText color="danger">{errors.libraAmount.message}</FormText>}
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
                value={libraAmount ? libraToHumanFriendly(calcPrice(libraAmount)) : ""}
                onChange={(e) => {
                  if (e.target === document.activeElement) {
                    const value = parseFloat(e.target.value);
                    const newPrice = libraFromFloat(value || 0);
                    const amount = normalizeLibra(calcAmount(newPrice));
                    setValue("libraAmount", amount);
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
            1 {fromCurrency.sign} = {libraToHumanFriendly(exchangeRate)} {toCurrency.sign}
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
