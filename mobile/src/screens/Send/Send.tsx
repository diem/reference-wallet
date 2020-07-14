// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useRef } from "react";
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
} from "../../utils/dropdown-options";
import { fiatCurrencies, libraCurrencies } from "../../currencies";
import {
  fiatFromFloat,
  fiatToHumanFriendly,
  fiatToHumanFriendlyRate,
  libraToFloat,
  normalizeLibra,
} from "../../utils/amount-precision";
import InputErrorMessage from "../../components/InputErrorMessage";

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

interface SendData extends Record<string, any> {
  libraCurrency?: LibraCurrency;
  fiatCurrency: FiatCurrency;
  libraAmount?: string;
  libraAddress?: string;
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

  function setAddressAndIntents(value: string) {
    const parsedAddress = parseLibraAddress(value);

    setValue("libraAddress", parsedAddress.address);

    if (parsedAddress.currency) {
      setValue("libraCurrency", parsedAddress.currency);
    }

    if (parsedAddress.amount) {
      setValue("libraAmount", parsedAddress.amount.toString());
    }
  }

  async function onFormSubmit({
    fiatCurrency,
    libraCurrency,
    libraAmount,
    libraAddress,
  }: SendData) {
    await Navigation.push(componentId, {
      component: {
        name: "SendReview",
        passProps: {
          fiatCurrencyCode: fiatCurrency,
          libraCurrencyCode: libraCurrency,
          libraAmount,
          libraAddress,
        },
      },
    });
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
                  <Text style={{ textTransform: "capitalize" }}>{t("form.libraCurrency")}</Text>
                  <Controller
                    control={control}
                    name="libraCurrency"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("form.libraCurrency") },
                      }),
                    }}
                    onChangeName="onChange"
                    as={
                      <SelectDropdown
                        label={t("form.libraCurrency_placeholder")}
                        options={libraCurrenciesWithBalanceOptions(account.balances)}
                      />
                    }
                  />
                  {!!errors.libraCurrency && (
                    <InputErrorMessage message={errors.libraCurrency.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("form.address")}</Text>
                  <Controller
                    control={control}
                    name="libraAddress"
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
                        rightIcon={{
                          name: "camera",
                          onPress: () => {
                            Navigation.push(componentId, {
                              component: {
                                name: "SendScanQR",
                                passProps: {
                                  callback: setAddressAndIntents,
                                },
                              },
                            });
                          },
                        }}
                      />
                    }
                  />
                  {!!errors.libraAddress && (
                    <InputErrorMessage message={errors.libraAddress.message as string} />
                  )}
                </View>

                <View style={theme.Section}>
                  <Text style={{ textTransform: "capitalize" }}>{t("form.amount")}</Text>
                  <Controller
                    control={control}
                    name="libraAmount"
                    rules={{
                      required: t<string>("validations:required", {
                        replace: { field: t("form.amount") },
                      }),
                    }}
                    onChangeName="onChangeText"
                    as={
                      <Input
                        disabled={!libraCurrency || !fiatCurrency}
                        keyboardType="numeric"
                        placeholder={t("form.amount")}
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
                  <Text style={{ textTransform: "capitalize" }}>{t("form.price")}</Text>
                  <Input
                    ref={priceRef}
                    disabled={!libraCurrency || !fiatCurrency}
                    keyboardType="numeric"
                    renderErrorMessage={false}
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

                {libraCurrency && fiatCurrency && (
                  <View style={theme.Section}>
                    <Text style={{ textTransform: "capitalize" }}>{t("form.exchange_rate")}</Text>
                    <Text>
                      1 {libraCurrency.sign} = {fiatToHumanFriendlyRate(exchangeRate)}{" "}
                      {fiatCurrency.symbol}
                    </Text>
                  </View>
                )}

                <Button title={t("form.review")} onPress={handleSubmit(onFormSubmit)} />
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
