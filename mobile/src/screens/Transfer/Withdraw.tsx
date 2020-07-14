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
import { FiatCurrency, LibraCurrency } from "../../interfaces/currencies";
import SelectDropdown from "../../components/Select";
import {
  fiatCurrenciesOptions,
  libraCurrenciesWithBalanceOptions,
  paymentMethodOptions,
} from "../../utils/dropdown-options";
import { fiatCurrencies, libraCurrencies } from "../../currencies";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  fiatToHumanFriendlyRate,
  libraFromFloat,
  normalizeLibra,
} from "../../utils/amount-precision";
import InputErrorMessage from "../../components/InputErrorMessage";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import BackendClient from "../../services/backendClient";
import SessionStorage from "../../services/sessionStorage";

interface WithdrawData extends Record<string, any> {
  fundingSource?: number;
  fiatCurrency: FiatCurrency;
  libraCurrency?: LibraCurrency;
  libraAmount?: string;
}

function Withdraw({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("transfer");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const { errors, handleSubmit, control, setValue, watch } = useForm<WithdrawData>();
  const [errorMessage, setErrorMessage] = useState<string>();

  const libraAmount = watch("libraAmount") || 0;
  const libraCurrencyCode = watch("libraCurrency");
  const fiatCurrencyCode = watch("fiatCurrency");

  const priceRef = useRef<Input>(null);

  const libraCurrency = libraCurrencyCode ? libraCurrencies[libraCurrencyCode] : undefined;
  const fiatCurrency = fiatCurrencyCode ? fiatCurrencies[fiatCurrencyCode] : undefined;

  const exchangeRate =
    rates && libraCurrencyCode && fiatCurrencyCode ? rates[libraCurrencyCode][fiatCurrencyCode] : 0;

  function calcPrice(libraAmount: number) {
    return libraAmount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  async function onFormSubmit({
    fundingSource,
    fiatCurrency,
    libraCurrency,
    libraAmount,
  }: WithdrawData) {
    try {
      setErrorMessage(undefined);
      const token = await SessionStorage.getAccessToken();
      const quote = await new BackendClient(token).requestWithdrawQuote(
        libraCurrency!,
        fiatCurrency!,
        libraFromFloat(parseFloat(libraAmount!))
      );
      await Navigation.push(componentId, {
        component: {
          name: "WithdrawReview",
          passProps: {
            quote,
            fundingSourceId: fundingSource,
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
                  {t("withdraw.form.title")}
                </Text>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>
                    {t("withdraw.form.funding_source")}
                  </Text>
                  <Controller
                    control={control}
                    name="fundingSource"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("withdraw.form.funding_source_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("withdraw.form.funding_source_placeholder")}
                        options={paymentMethodOptions(user.paymentMethods || [])}
                      />
                    }
                  />
                  {!!errors.fundingSource && (
                    <InputErrorMessage message={errors.fundingSource.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("withdraw.form.currency")}</Text>
                  <Controller
                    control={control}
                    name="libraCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("withdraw.form.currency_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("withdraw.form.currency_placeholder")}
                        options={libraCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.libraCurrency && (
                    <InputErrorMessage message={errors.libraCurrency.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("withdraw.form.amount")}</Text>
                  <Controller
                    control={control}
                    name="libraAmount"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("withdraw.form.amount") },
                      }),
                    }}
                    onChangeName="onChangeText"
                    as={
                      <Input
                        keyboardType="numeric"
                        placeholder={t("withdraw.form.amount")}
                        renderErrorMessage={false}
                        rightIcon={<Text>{libraCurrency?.sign}</Text>}
                      />
                    }
                  />
                  {!!errors.libraAmount && (
                    <InputErrorMessage message={errors.libraAmount.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("withdraw.form.price")}</Text>
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
                    rightIcon={
                      <Controller
                        control={control}
                        name="fiatCurrency"
                        rules={{
                          required: t<string>("validations:required", {
                            replace: { field: t("withdraw.form.fiatCurrency") },
                          }),
                        }}
                        onChangeName="onChange"
                        as={
                          <SelectDropdown
                            label={t("withdraw.form.currency_placeholder")}
                            options={fiatCurrenciesOptions()}
                            disableStyles={true}
                          />
                        }
                      />
                    }
                  />
                  {!!errors.fiatCurrency && (
                    <InputErrorMessage message={errors.fiatCurrency.message as string} />
                  )}
                </View>

                {libraCurrency && fiatCurrency && (
                  <View style={theme.Section}>
                    <Text style={{ textTransform: "capitalize" }}>
                      {t("withdraw.form.exchange_rate")}
                    </Text>
                    <Text>
                      1 {libraCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)}{" "}
                      {fiatCurrency.symbol}
                    </Text>
                  </View>
                )}

                <Button title={t("withdraw.form.review")} onPress={handleSubmit(onFormSubmit)} />
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

export default withRatesContext(withAccountContext(withUserContext(Withdraw)));
