// Copyright (c) The Libra Core Contributors
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
import { FiatCurrency, LibraCurrency } from "../../interfaces/currencies";
import { Send } from "./interfaces";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  fiatToHumanFriendlyRate,
  libraFromFloat,
  libraToFloat,
  normalizeLibra,
} from "../../utils/amount-precision";
import {
  fiatCurrenciesOptions,
  libraCurrenciesWithBalanceOptions,
} from "../../utils/dropdown-options";

const VALID_VASP_ADDRESS_REGEX = new RegExp("^[a-zA-Z0-9]{50}$");
const LIBRA_PREFIX = "libra://";

interface AddressWithIntents {
  address: string;
  currency?: LibraCurrency;
  amount?: number;
}

function parseLibraAddress(address: string): AddressWithIntents {
  let amount: number | undefined = undefined;
  let currency: LibraCurrency | undefined = undefined;
  if (address.startsWith(LIBRA_PREFIX)) {
    address = address.substring(LIBRA_PREFIX.length);
  }

  const parts = address.split("?", 2);
  if (parts.length > 1) {
    const intents = parts[1].split("&");
    intents.forEach((intent) => {
      const [key, value] = intent.split("=", 2);
      switch (key) {
        case "c":
          currency = decodeURIComponent(value) as LibraCurrency;
          break;
        case "am":
          amount = libraToFloat(parseInt(decodeURIComponent(value)));
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

  const [selectedLibraCurrency, setSelectedLibraCurrency] = useState<LibraCurrency | undefined>(
    value.libraCurrency
  );
  const [selectedFiatCurrency, setSelectedFiatCurrency] = useState<FiatCurrency>(
    value.fiatCurrency
  );
  const libraAmount = watch("libraAmount") || 0;
  const priceRef = useRef<HTMLInputElement>(null);

  const libraCurrency = selectedLibraCurrency
    ? settings.currencies[selectedLibraCurrency]
    : undefined;

  const fiatCurrency = selectedFiatCurrency
    ? settings.fiatCurrencies[selectedFiatCurrency]
    : undefined;

  const exchangeRate = libraCurrency?.rates[selectedFiatCurrency] || 0;

  function calcPrice(libraAmount: number) {
    return libraAmount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  function setAddressAndIntents(value: string) {
    const parsedAddress = parseLibraAddress(value);

    setValue("libraAddress", parsedAddress.address);

    if (parsedAddress.currency) {
      setSelectedLibraCurrency(parsedAddress.currency);
      setValue("libraCurrency", parsedAddress.currency);
    }

    if (parsedAddress.amount) setValue("libraAmount", parsedAddress.amount);
  }

  return (
    <Form onSubmit={handleSubmit(onSubmit)}>
      <h3>{t("form.title")}</h3>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("form.libraCurrency")}</FormText>
        <Controller
          invalid={!!errors.libraCurrency}
          control={control}
          name="libraCurrency"
          rules={{
            required: (
              <Trans i18nKey="validations:required" values={{ field: t("form.libraCurrency") }} />
            ),
          }}
          defaultValue={value.libraCurrency}
          onChange={([val]) => {
            setSelectedLibraCurrency(val);
            return val;
          }}
          as={
            <SelectDropdown
              label={t("form.libraCurrency_placeholder")}
              options={libraCurrenciesWithBalanceOptions(
                settings.currencies,
                settings.account!.balances
              )}
            />
          }
        />
        {errors.libraCurrency && <FormText color="danger">{errors.libraCurrency.message}</FormText>}
      </FormGroup>
      <FormGroup>
        <FormText className="text-capitalize-first">{t("form.address")}</FormText>
        <Input
          invalid={!!errors.libraAddress}
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
          name="libraAddress"
          type="text"
          placeholder={t("form.address_placeholder")}
          defaultValue={value.libraAddress}
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
        {errors.libraAddress && <FormText color="danger">{errors.libraAddress.message}</FormText>}
      </FormGroup>
      <Row>
        <Col sm="6">
          <FormGroup>
            <FormText className="text-capitalize-first">{t("form.amount")}</FormText>
            <InputGroup>
              <Controller
                invalid={!!errors.libraAmount}
                control={control}
                name="libraAmount"
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
                    const selectedLibraCurrency = watch("libraCurrency");

                    if (selectedLibraCurrency) {
                      const selectedCurrencyBalance = settings.account!.balances.find(
                        (balance) => balance.currency === selectedLibraCurrency
                      )!;
                      if (libraFromFloat(enteredAmount) > selectedCurrencyBalance.balance) {
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
                disabled={!selectedLibraCurrency}
                as={<Input min={0} step="any" type="number" />}
              />
              {libraCurrency && (
                <InputGroupAddon addonType="append">
                  <InputGroupText>{libraCurrency.sign}</InputGroupText>
                </InputGroupAddon>
              )}
            </InputGroup>
            {errors.libraAmount && <FormText color="danger">{errors.libraAmount.message}</FormText>}
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
                value={libraAmount ? fiatToHumanFriendly(calcPrice(libraAmount)) : ""}
                onValueChange={(values) => {
                  if (priceRef.current === document.activeElement) {
                    const newPrice = fiatFromFloat(values.floatValue || 0);
                    const amount = normalizeLibra(calcAmount(newPrice));
                    setValue("libraAmount", amount);
                  }
                }}
                disabled={!selectedLibraCurrency}
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
      {libraCurrency && fiatCurrency && (
        <FormGroup>
          <FormText className="text-capitalize-first">{t("form.exchange_rate")}</FormText>
          <p className="text-black">
            1 {libraCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)} {fiatCurrency.symbol}
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
