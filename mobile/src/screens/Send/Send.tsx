// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useRef, useState } from "react";
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
} from "../../utils/dropdown-options";
import { fiatCurrencies, diemCurrencies } from "../../currencies";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  fiatToHumanFriendlyRate,
  diemFromFloat,
  diemToFloat,
  normalizeDiem,
} from "../../utils/amount-precision";
import InputErrorMessage from "../../components/InputErrorMessage";
// @ts-ignore
import ScanQR from "../../assets/scan-qr.svg";

const VALID_VASP_ADDRESS_REGEX = new RegExp("^[a-zA-Z0-9]{50}$");
const LIBRA_PREFIX = "diem://";

interface AddressWithIntents {
  address: string;
  currency?: DiemCurrency;
  amount?: number;
}

function parseDiemAddress(address: string): AddressWithIntents {
  let amount: number | undefined = undefined;
  let currency: DiemCurrency | undefined = undefined;
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
          currency = decodeURIComponent(value) as DiemCurrency;
          break;
        case "am":
          amount = diemToFloat(parseInt(decodeURIComponent(value)));
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

interface SendData extends Record<string, any> {
  diemCurrency?: DiemCurrency;
  fiatCurrency: FiatCurrency;
  diemAmount?: string;
  diemAddress?: string;
}

interface SendProps {
  addressWithIntents?: string;
}

function Send({ componentId, addressWithIntents }: SendProps & NavigationComponentProps) {
  const { t } = useTranslation("send");

  const user = useContext(userContext);
  const account = useContext(accountContext);
  const rates = useContext(ratesContext);

  const { errors, handleSubmit, control, setValue, watch } = useForm<SendData>();
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

  function setAddressAndIntents(value: string) {
    const parsedAddress = parseDiemAddress(value);

    setValue("diemAddress", parsedAddress.address);

    if (parsedAddress.currency) {
      setValue("diemCurrency", parsedAddress.currency);
    }

    if (parsedAddress.amount) {
      setValue("diemAmount", parsedAddress.amount.toString());
    }
  }

  async function onFormSubmit({
    fiatCurrency,
    diemCurrency,
    diemAmount,
    diemAddress,
  }: SendData) {
    setLoading(true);
    Keyboard.dismiss();
    await Navigation.push(componentId, {
      component: {
        name: "SendReview",
        passProps: {
          fiatCurrencyCode: fiatCurrency,
          diemCurrencyCode: diemCurrency,
          diemAmount,
          diemAddress,
        },
      },
    });
    setLoading(false);
  }

  useEffect(() => {
    if (addressWithIntents) {
      setAddressAndIntents(addressWithIntents);
    }
  });

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            {user && account && rates ? (
              <View style={theme.Container}>
                <Text style={StyleSheet.flatten([theme.Title, theme.Section])}>
                  {t("form.title")}
                </Text>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("form.diemCurrency")}</Text>
                  <Controller
                    control={control}
                    name="diemCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("form.diemCurrency") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("form.diemCurrency_placeholder")}
                        options={diemCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.diemCurrency && (
                    <InputErrorMessage message={errors.diemCurrency.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("form.address")}</Text>
                  <Controller
                    control={control}
                    name="diemAddress"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("form.address") },
                      }),
                      pattern: {
                        value: VALID_VASP_ADDRESS_REGEX,
                        message: t<string>("validations:pattern", {
                          replace: { field: t("form.address") },
                        }),
                      },
                    }}
                    onChangeName="onChangeText"
                    as={
                      <Input
                        placeholder={t("form.address_placeholder")}
                        renderErrorMessage={false}
                        onEndEditing={(e) => {
                          const value = e.nativeEvent.text;
                          setAddressAndIntents(value);
                        }}
                        rightIcon={
                          <ScanQR
                            onPress={() => {
                              Navigation.push(componentId, {
                                component: {
                                  name: "SendScanQR",
                                  passProps: {
                                    callback: setAddressAndIntents,
                                  },
                                },
                              });
                            }}
                          />
                        }
                      />
                    }
                  />
                  {!!errors.diemAddress && (
                    <InputErrorMessage message={errors.diemAddress.message as string} />
                  )}
                </View>

                <View
                  style={StyleSheet.flatten([theme.Section, theme.ButtonsGroup.containerStyle])}
                >
                  <View style={theme.ButtonsGroup.buttonStyle}>
                    <Text style={{ textTransform: "capitalize" }}>{t("form.amount")}</Text>
                    <Controller
                      control={control}
                      name="diemAmount"
                      rules={{
                        validate: (enteredAmount) => {
                          if (!isFinite(Number(enteredAmount)) || parseFloat(enteredAmount) < 1) {
                            return t<string>("validations:min", {
                              replace: { field: t("form.amount"), min: 1 },
                            });
                          }

                          const selectedDiemCurrency = watch("diemCurrency");

                          if (selectedDiemCurrency) {
                            const selectedCurrencyBalance = account!.balances.find(
                              (balance) => balance.currency === selectedDiemCurrency
                            )!;
                            if (diemFromFloat(enteredAmount) > selectedCurrencyBalance.balance) {
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
                      onChangeName="onChangeText"
                      as={
                        <Input
                          keyboardType="numeric"
                          placeholder={t("form.amount")}
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
                    <Text style={{ textTransform: "capitalize" }}>{t("form.price")}</Text>
                    <Input
                      ref={priceRef}
                      disabled={!diemCurrency || !fiatCurrency}
                      keyboardType="numeric"
                      renderErrorMessage={false}
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
                              replace: { field: t("form.fiatCurrency") },
                            }),
                          }}
                          onChangeName="onChange"
                          as={
                            <SelectDropdown
                              label={t("form.fiatCurrency")}
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
                    <Text style={{ textTransform: "capitalize" }}>{t("form.exchange_rate")}</Text>
                    <Text>
                      1 {diemCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)}{" "}
                      {fiatCurrency.symbol}
                    </Text>
                  </View>
                )}

                <Button
                  title={t("form.review")}
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

export default withRatesContext(withAccountContext(withUserContext(Send)));
