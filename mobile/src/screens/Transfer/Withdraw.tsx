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
import { FiatCurrency, DiemCurrency } from "../../interfaces/currencies";
import SelectDropdown from "../../components/Select";
import {
  fiatCurrenciesOptions,
  diemCurrenciesWithBalanceOptions,
  paymentMethodOptions,
} from "../../utils/dropdown-options";
import { fiatCurrencies, diemCurrencies } from "../../currencies";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  fiatToHumanFriendlyRate,
  diemFromFloat,
  normalizeDiem,
} from "../../utils/amount-precision";
import InputErrorMessage from "../../components/InputErrorMessage";
import { BackendError } from "../../services/errors";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import BackendClient from "../../services/backendClient";
import SessionStorage from "../../services/sessionStorage";

interface WithdrawData extends Record<string, any> {
  fundingSource?: number;
  fiatCurrency: FiatCurrency;
  diemCurrency?: DiemCurrency;
  diemAmount?: string;
}

function Withdraw({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("transfer");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const { errors, handleSubmit, control, setValue, watch } = useForm<WithdrawData>();
  const [errorMessage, setErrorMessage] = useState<string>();
  const [loading, setLoading] = useState<boolean>(false);

  const diemAmount = watch("diemAmount") || 0;
  const diemCurrencyCode = watch("diemCurrency");
  const fiatCurrencyCode = watch("fiatCurrency");

  const priceRef = useRef<Input>(null);

  const diemCurrency = diemCurrencyCode ? diemCurrencies[diemCurrencyCode] : undefined;
  const fiatCurrency = fiatCurrencyCode
    ? fiatCurrencies[fiatCurrencyCode]
    : fiatCurrencies[user!.selected_fiat_currency];

  const exchangeRate =
    rates && diemCurrencyCode && fiatCurrencyCode ? rates[diemCurrencyCode][fiatCurrencyCode] : 0;

  function calcPrice(diemAmount: number) {
    return diemAmount * exchangeRate;
  }

  function calcAmount(price: number) {
    return price / exchangeRate;
  }

  async function onFormSubmit({
    fundingSource,
    fiatCurrency,
    diemCurrency,
    diemAmount,
  }: WithdrawData) {
    setLoading(true);
    Keyboard.dismiss();
    try {
      setErrorMessage(undefined);
      const token = await SessionStorage.getAccessToken();
      const quote = await new BackendClient(token).requestWithdrawQuote(
        diemCurrency!,
        fiatCurrency!,
        diemFromFloat(parseFloat(diemAmount!))
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
                  {t("withdraw.form.title")}
                </Text>

                <View style={theme.Section}>
                  <Text>{t("withdraw.form.funding_source")}</Text>
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
                  {!user.paymentMethods?.length && (
                    <Text
                      style={{ color: theme.colors!.error }}
                      onPress={() => {
                        Navigation.push(componentId, {
                          component: {
                            name: "Settings",
                          },
                        });
                      }}
                    >
                      {t("deposit.form.no_funding_sources")}
                    </Text>
                  )}
                </View>

                <View style={theme.Section}>
                  <Text>{t("withdraw.form.currency")}</Text>
                  <Controller
                    control={control}
                    name="diemCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("withdraw.form.currency_placeholder") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("withdraw.form.currency_placeholder")}
                        options={diemCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.diemCurrency && (
                    <InputErrorMessage message={errors.diemCurrency.message as string} />
                  )}
                </View>

                <View
                  style={StyleSheet.flatten([theme.Section, theme.ButtonsGroup.containerStyle])}
                >
                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text>{t("withdraw.form.amount")}</Text>
                    <Controller
                      control={control}
                      name="diemAmount"
                      rules={{
                        validate: (value) => {
                          if (!isFinite(Number(value)) || parseFloat(value) < 1) {
                            return t<string>("validations:min", {
                              replace: { field: t("withdraw.form.amount"), min: 1 },
                            });
                          }

                          const selectedDiemCurrency = watch("diemCurrency");
                          if (selectedDiemCurrency) {
                            const selectedCurrencyBalance = account!.balances.find(
                              (balance) => balance.currency === selectedDiemCurrency
                            )!;
                            if (diemFromFloat(value) > selectedCurrencyBalance.balance) {
                              return t("validations:noMoreThanBalance", {
                                replace: {
                                  field: t("withdraw.form.amount"),
                                  currency: selectedCurrencyBalance.currency,
                                },
                              })!;
                            }
                          }
                        },
                      }}
                      onChangeName="onChangeText"
                      as={
                        <Input
                          keyboardType="numeric"
                          placeholder={t("withdraw.form.amount")}
                          renderErrorMessage={false}
                          rightIcon={<Text>{diemCurrency?.sign}</Text>}
                        />
                      }
                    />
                    {!!errors.diemAmount && (
                      <InputErrorMessage message={errors.diemAmount.message as string} />
                    )}
                  </View>

                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text>{t("withdraw.form.price")}</Text>
                    <Input
                      ref={priceRef}
                      keyboardType="numeric"
                      value={
                        diemAmount && isFinite(Number(diemAmount))
                          ? fiatToHumanFriendly(calcPrice(parseFloat(diemAmount)))
                          : ""
                      }
                      onChangeText={(price) => {
                        if (
                          priceRef.current &&
                          priceRef.current.isFocused() &&
                          isFinite(Number(price)) &&
                          exchangeRate > 0
                        ) {
                          const newPrice = fiatFromFloat(parseFloat(price));
                          const amount = normalizeDiem(calcAmount(newPrice));
                          setValue("diemAmount", amount.toString());
                        }
                      }}
                      rightIcon={
                        <Controller
                          control={control}
                          name="fiatCurrency"
                          defaultValue={fiatCurrency.symbol}
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
                </View>

                {diemCurrency && fiatCurrency && (
                  <View style={theme.Section}>
                    <Text>{t("withdraw.form.exchange_rate")}</Text>
                    <Text>
                      1 {diemCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)}{" "}
                      {fiatCurrency.symbol}
                    </Text>
                  </View>
                )}

                <Button
                  title={t("withdraw.form.review")}
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

export default withRatesContext(withAccountContext(withUserContext(Withdraw)));
