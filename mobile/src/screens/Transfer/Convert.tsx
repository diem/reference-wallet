// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useRef, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import { userContext, withUserContext } from "../../contexts/user";
import { accountContext, withAccountContext } from "../../contexts/account";
import ScreenLayout from "../../components/ScreenLayout";
import { appTheme } from "../../styles";
import { ratesContext, withRatesContext } from "../../contexts/rates";
import { LibraCurrency } from "../../interfaces/currencies";
import SelectDropdown from "../../components/Select";
import { libraCurrenciesWithBalanceOptions } from "../../utils/dropdown-options";
import { libraCurrencies } from "../../currencies";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  libraFromFloat,
  libraToHumanFriendly,
  normalizeLibra,
} from "../../utils/amount-precision";
import InputErrorMessage from "../../components/InputErrorMessage";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import BackendClient from "../../services/backendClient";
import SessionStorage from "../../services/sessionStorage";

interface ConvertData extends Record<string, any> {
  fromLibraCurrency?: LibraCurrency;
  toLibraCurrency?: LibraCurrency;
  libraAmount?: string;
}

function Convert({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("transfer");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const { errors, handleSubmit, control, setValue, watch } = useForm<ConvertData>();
  const [errorMessage, setErrorMessage] = useState<string>();

  const libraAmount = watch("libraAmount") || 0;
  const fromLibraCurrencyCode = watch("fromLibraCurrency");
  const toLibraCurrencyCode = watch("toLibraCurrency");

  const priceRef = useRef<Input>(null);

  const fromLibraCurrency = fromLibraCurrencyCode
    ? libraCurrencies[fromLibraCurrencyCode]
    : undefined;
  const toLibraCurrency = toLibraCurrencyCode ? libraCurrencies[toLibraCurrencyCode] : undefined;

  const exchangeRate =
    rates && fromLibraCurrencyCode && toLibraCurrencyCode
      ? rates[fromLibraCurrencyCode][toLibraCurrencyCode]
      : 0;

  function calcPrice(libraAmount: number) {
    return libraAmount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  async function onFormSubmit({ fromLibraCurrency, toLibraCurrency, libraAmount }: ConvertData) {
    try {
      setErrorMessage(undefined);
      const token = await SessionStorage.getAccessToken();
      const quote = await new BackendClient(token).requestConvertQuote(
        fromLibraCurrency!,
        toLibraCurrency!,
        libraFromFloat(parseFloat(libraAmount!))
      );
      await Navigation.push(componentId, {
        component: {
          name: "ConvertReview",
          passProps: {
            quote,
          },
        },
      });
    } catch (e) {
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected Error", e);
      }
    }
  }

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            {user && account && rates ? (
              <View style={theme.Container}>
                {errorMessage && <ErrorMessage message={errorMessage} />}

                <Text style={StyleSheet.flatten([theme.Title, theme.Section])}>
                  {t("convert.form.title")}
                </Text>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>
                    {t("convert.form.currency_from")}
                  </Text>
                  <Controller
                    control={control}
                    name="fromLibraCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("convert.form.currency_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("convert.form.currency_placeholder")}
                        options={libraCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.fromLibraCurrency && (
                    <InputErrorMessage message={errors.fromLibraCurrency.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>
                    {t("convert.form.currency_to")}
                  </Text>
                  <Controller
                    control={control}
                    name="toLibraCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("convert.form.currency_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("convert.form.currency_placeholder")}
                        options={libraCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.toLibraCurrency && (
                    <InputErrorMessage message={errors.toLibraCurrency.message as string} />
                  )}
                </View>

                <View
                  style={StyleSheet.flatten([theme.Section, theme.ButtonsGroup.containerStyle])}
                >
                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text style={{ textTransform: "capitalize" }}>{t("convert.form.amount")}</Text>
                    <Controller
                      control={control}
                      name="libraAmount"
                      rules={{
                        required: t<string>("validations:required", {
                          replace: { field: t("convert.form.amount") },
                        }),
                        min: {
                          value: 1,
                          message: t<string>("validations:min", {
                            replace: { field: t("convert.form.amount"), min: 1 },
                          }),
                        },
                        validate: (enteredAmount: number) => {
                          const selectedFromLibraCurrency = watch("fromLibraCurrency");

                          if (selectedFromLibraCurrency) {
                            const selectedCurrencyBalance = account!.balances.find(
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
                      onChangeName="onChangeText"
                      as={
                        <Input
                          keyboardType="numeric"
                          placeholder={t("convert.form.amount")}
                          renderErrorMessage={false}
                          rightIcon={<Text>{fromLibraCurrency?.sign}</Text>}
                        />
                      }
                    />
                    {!!errors.libraAmount && (
                      <InputErrorMessage message={errors.libraAmount.message as string} />
                    )}
                  </View>

                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text style={{ textTransform: "capitalize" }}>{t("convert.form.price")}</Text>
                    <Input
                      ref={priceRef}
                      keyboardType="numeric"
                      value={
                        libraAmount ? fiatToHumanFriendly(calcPrice(parseFloat(libraAmount))) : ""
                      }
                      onChangeText={(price) => {
                        if (priceRef.current && priceRef.current.isFocused()) {
                          const newPrice = fiatFromFloat(parseFloat(price));
                          const amount = normalizeLibra(calcAmount(newPrice));
                          setValue("libraAmount", amount.toString());
                        }
                      }}
                      renderErrorMessage={false}
                      rightIcon={<Text>{toLibraCurrency?.sign}</Text>}
                    />
                    {!!errors.fiatCurrency && (
                      <InputErrorMessage message={errors.fiatCurrency.message as string} />
                    )}
                  </View>
                </View>

                {fromLibraCurrency && toLibraCurrency && (
                  <View style={theme.Section}>
                    <Text style={{ textTransform: "capitalize" }}>
                      {t("convert.form.exchange_rate")}
                    </Text>
                    <Text>
                      1 {fromLibraCurrency.sign} = {libraToHumanFriendly(exchangeRate)}{" "}
                      {toLibraCurrency.sign}
                    </Text>
                  </View>
                )}

                <Button title={t("convert.form.review")} onPress={handleSubmit(onFormSubmit)} />
              </View>
            ) : (
              <ActivityIndicator size="large" />
            )}
          </>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withRatesContext(withAccountContext(withUserContext(Convert)));
