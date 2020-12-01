// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useRef, useState } from "react";
import { ActivityIndicator, Keyboard, StyleSheet, View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { Controller, useForm } from "react-hook-form";
import { userContext, withUserContext } from "../../contexts/user";
import { accountContext, withAccountContext } from "../../contexts/account";
import ScreenLayout from "../../components/ScreenLayout";
import { appTheme } from "../../styles";
import { ratesContext, withRatesContext } from "../../contexts/rates";
import { DiemCurrency } from "../../interfaces/currencies";
import SelectDropdown from "../../components/Select";
import { diemCurrenciesWithBalanceOptions } from "../../utils/dropdown-options";
import { diemCurrencies } from "../../currencies";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  diemFromFloat,
  diemToHumanFriendly,
  normalizeDiem,
} from "../../utils/amount-precision";
import InputErrorMessage from "../../components/InputErrorMessage";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import BackendClient from "../../services/backendClient";
import SessionStorage from "../../services/sessionStorage";

interface ConvertData extends Record<string, any> {
  fromDiemCurrency?: DiemCurrency;
  toDiemCurrency?: DiemCurrency;
  diemAmount?: string;
}

function Convert({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("transfer");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const { errors, handleSubmit, control, setValue, watch } = useForm<ConvertData>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [loading, setLoading] = useState<boolean>(false);

  const diemAmount = watch("diemAmount") || 0;
  const fromDiemCurrencyCode = watch("fromDiemCurrency");
  const toDiemCurrencyCode = watch("toDiemCurrency");

  const priceRef = useRef<Input>(null);

  const fromDiemCurrency = fromDiemCurrencyCode
    ? diemCurrencies[fromDiemCurrencyCode]
    : undefined;
  const toDiemCurrency = toDiemCurrencyCode ? diemCurrencies[toDiemCurrencyCode] : undefined;

  const exchangeRate =
    rates && fromDiemCurrencyCode && toDiemCurrencyCode
      ? rates[fromDiemCurrencyCode][toDiemCurrencyCode]
      : 0;

  function calcPrice(diemAmount: number) {
    return diemAmount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  async function onFormSubmit({ fromDiemCurrency, toDiemCurrency, diemAmount }: ConvertData) {
    setLoading(true);
    Keyboard.dismiss();
    try {
      setErrorMessage(undefined);
      const token = await SessionStorage.getAccessToken();
      const quote = await new BackendClient(token).requestConvertQuote(
        fromDiemCurrency!,
        toDiemCurrency!,
        diemFromFloat(parseFloat(diemAmount!))
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
    setLoading(false);
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
                  <Text>{t("convert.form.currency_from")}</Text>
                  <Controller
                    control={control}
                    name="fromDiemCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("convert.form.currency_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("convert.form.currency_placeholder")}
                        options={diemCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.fromDiemCurrency && (
                    <InputErrorMessage message={errors.fromDiemCurrency.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text>{t("convert.form.currency_to")}</Text>
                  <Controller
                    control={control}
                    name="toDiemCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("convert.form.currency_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("convert.form.currency_placeholder")}
                        options={diemCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.toDiemCurrency && (
                    <InputErrorMessage message={errors.toDiemCurrency.message as string} />
                  )}
                </View>

                <View
                  style={StyleSheet.flatten([theme.Section, theme.ButtonsGroup.containerStyle])}
                >
                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text>{t("convert.form.amount")}</Text>
                    <Controller
                      control={control}
                      name="diemAmount"
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
                          const selectedFromDiemCurrency = watch("fromDiemCurrency");

                          if (selectedFromDiemCurrency) {
                            const selectedCurrencyBalance = account!.balances.find(
                              (balance) => balance.currency === selectedFromDiemCurrency
                            )!;
                            if (diemFromFloat(enteredAmount) > selectedCurrencyBalance.balance) {
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
                          rightIcon={<Text>{fromDiemCurrency?.sign}</Text>}
                        />
                      }
                    />
                    {!!errors.diemAmount && (
                      <InputErrorMessage message={errors.diemAmount.message as string} />
                    )}
                  </View>

                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text>{t("convert.form.price")}</Text>
                    <Input
                      ref={priceRef}
                      keyboardType="numeric"
                      value={
                        diemAmount ? fiatToHumanFriendly(calcPrice(parseFloat(diemAmount))) : ""
                      }
                      onChangeText={(price) => {
                        if (priceRef.current && priceRef.current.isFocused()) {
                          const newPrice = fiatFromFloat(parseFloat(price));
                          const amount = normalizeDiem(calcAmount(newPrice));
                          setValue("diemAmount", amount.toString());
                        }
                      }}
                      renderErrorMessage={false}
                      rightIcon={<Text>{toDiemCurrency?.sign}</Text>}
                    />
                    {!!errors.fiatCurrency && (
                      <InputErrorMessage message={errors.fiatCurrency.message as string} />
                    )}
                  </View>
                </View>

                {fromDiemCurrency && toDiemCurrency && (
                  <View style={theme.Section}>
                    <Text>{t("convert.form.exchange_rate")}</Text>
                    <Text>
                      1 {fromDiemCurrency.sign} = {diemToHumanFriendly(exchangeRate)}{" "}
                      {toDiemCurrency.sign}
                    </Text>
                  </View>
                )}

                <Button
                  title={t("convert.form.review")}
                  onPress={handleSubmit(onFormSubmit)}
                  loading={loading}
                />
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
