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
import { Controller, useForm } from "react-hook-form";
import NumberInput from "react-number-format";
import SelectDropdown from "../select";
import { settingsContext } from "../../contexts/app";
import { FiatCurrency, Currency } from "../../interfaces/currencies";
import { Send } from "./interfaces";
import {
  fiatFromDiemFloat,
  fiatToDiemHumanFriendly,
  fiatToHumanFriendlyRate,
  diemAmountFromFloat,
  diemAmountToFloat,
  normalizeDiemAmount,
} from "../../utils/amount-precision";
import { fiatCurrenciesOptions, currenciesWithBalanceOptions } from "../../utils/dropdown-options";
import { ADDR_PROTOCOL_PREFIX, VALID_VASP_ADDRESS_REGEX } from "../../interfaces/blockchain";

interface AddressWithIntents {
  address: string;
  currency?: Currency;
  amount?: number;
}

function parseAddressIntents(address: string): AddressWithIntents {
  let amount: number | undefined = undefined;
  let currency: Currency | undefined = undefined;
  if (address.startsWith(ADDR_PROTOCOL_PREFIX)) {
    address = address.substring(ADDR_PROTOCOL_PREFIX.length);
  }

  const parts = address.split("?", 2);
  if (parts.length > 1) {
    const intents = parts[1].split("&");
    intents.forEach((intent) => {
      const [key, value] = intent.split("=", 2);
      switch (key) {
        case "c":
          currency = decodeURIComponent(value) as Currency;
          break;
        case "am":
          amount = diemAmountToFloat(parseInt(decodeURIComponent(value)));
          break;
      }
    });
    address = parts[0];
  }

  return {
    address,
    currency,
    amount,
  };
}

interface SendFormProps {
  value: Send;
  onSubmit: (value: Send) => void;
}

function SendForm({ value, onSubmit }: SendFormProps) {
  const { t } = useTranslation("send");
  const [settings] = useContext(settingsContext)!;
  const { register, errors, handleSubmit, control, setValue, watch } = useForm<Send>();

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

  const exchangeRate = currency?.rates[selectedFiatCurrency] || 0;

  function calcPrice(amount: number) {
    return amount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  function setAddressAndIntents(value: string) {
    const parsedAddress = parseAddressIntents(value);

    setValue("address", parsedAddress.address);

    if (parsedAddress.currency) {
      setSelectedCurrency(parsedAddress.currency);
      setValue("currency", parsedAddress.currency);
    }

    if (parsedAddress.amount) setValue("amount", parsedAddress.amount);
  }

  return (
    <Form onSubmit={handleSubmit(onSubmit)}>
      <h3>{t("form.title")}</h3>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("form.currency")}</FormText>
        <Controller
          invalid={!!errors.currency}
          control={control}
          name="currency"
          rules={{
            required: (
              <Trans i18nKey="validations:required" values={{ field: t("form.currency") }} />
            ),
          }}
          defaultValue={value.currency}
          onChange={([val]) => {
            setSelectedCurrency(val);
            return val;
          }}
          as={
            <SelectDropdown
              label={t("form.currency_placeholder")}
              options={currenciesWithBalanceOptions(
                settings.currencies,
                settings.account!.balances
              )}
            />
          }
        />
        {errors.currency && <FormText color="danger">{errors.currency.message}</FormText>}
      </FormGroup>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("form.address")}</FormText>
        <Input
          invalid={!!errors.address}
          innerRef={register({
            required: (
              <Trans i18nKey="validations:required" values={{ field: t("form.address") }} />
            ),
            pattern: {
              value: VALID_VASP_ADDRESS_REGEX,
              message: (
                <Trans i18nKey="validations:pattern" values={{ field: t("form.address") }} />
              ),
            },
          })}
          name="address"
          type="text"
          placeholder={t("form.address_placeholder")}
          defaultValue={value.address}
          onPaste={(e) => {
            e.preventDefault();
            const value = e.clipboardData.getData("Text");
            setAddressAndIntents(value);
          }}
          onBlur={(e) => {
            const value = e.target.value;
            setAddressAndIntents(value);
          }}
        />
        {errors.address && <FormText color="danger">{errors.address.message}</FormText>}
      </FormGroup>
      <Row>
        <Col sm="6">
          <FormGroup>
            <FormText className="text-capitalize-first">{t("form.amount")}</FormText>
            <InputGroup>
              <Controller
                invalid={!!errors.amount}
                control={control}
                name="amount"
                rules={{
                  required: (
                    <Trans i18nKey="validations:required" values={{ field: t("form.amount") }} />
                  ),
                  min: {
                    value: 0.0001,
                    message: (
                      <Trans
                        i18nKey="validations:min"
                        values={{ field: t("form.amount"), min: 0.0001 }}
                      />
                    ),
                  },
                  validate: (enteredAmount: number) => {
                    const selectedCurrency = watch("currency");

                    if (selectedCurrency) {
                      const selectedCurrencyBalance = settings.account!.balances.find(
                        (balance) => balance.currency === selectedCurrency
                      )!;
                      if (diemAmountFromFloat(enteredAmount) > selectedCurrencyBalance.balance) {
                        return t("validations:noMoreThanBalance", {
                          replace: {
                            field: t("form.amount"),
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
                disabled={!selectedCurrency}
                as={<Input min={0} step="any" type="number" />}
              />
              {currency && (
                <InputGroupAddon addonType="append">
                  <InputGroupText>{currency.sign}</InputGroupText>
                </InputGroupAddon>
              )}
            </InputGroup>
            {errors.amount && <FormText color="danger">{errors.amount.message}</FormText>}
          </FormGroup>
        </Col>
        <Col sm="6">
          <FormGroup>
            <FormText className="text-capitalize-first">{t("form.price")}</FormText>
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
                      values={{ field: t("form.fiatCurrency") }}
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
          <FormText className="text-capitalize-first">{t("form.exchange_rate")}</FormText>
          <p className="text-black">
            1 {currency.sign} = {fiatToHumanFriendlyRate(exchangeRate)} {fiatCurrency.symbol}
          </p>
        </FormGroup>
      )}
      <Button color="black" type="submit" block>
        {t("form.review")}
      </Button>
    </Form>
  );
}

export default SendForm;
