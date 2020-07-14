// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from "react-i18next";
import React from "react";
import { LibraCurrencyBalance } from "../interfaces/account";
import { Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";
import { View } from "react-native";
import { FiatCurrency, Rates } from "../interfaces/currencies";
import { fiatToHumanFriendly, libraToFloat, libraToHumanFriendly } from "../utils/amount-precision";
import { fiatCurrencies, libraCurrencies } from "../currencies";

interface TotalBalanceProps {
  balance: LibraCurrencyBalance;
  fiatCurrencyCode: FiatCurrency;
  rates: Rates;
}

function CurrencyBalance({ balance, fiatCurrencyCode, rates }: TotalBalanceProps) {
  const { t } = useTranslation("layout");

  const libraCurrency = libraCurrencies[balance.currency];
  const fiatCurrency = fiatCurrencies[fiatCurrencyCode];

  const exchangeRate = rates[balance.currency][fiatCurrencyCode];
  const price = libraToFloat(balance.balance) * exchangeRate;

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={{ ...theme.Section, alignItems: "center" }}>
          <Text style={theme.Title}>
            {libraToHumanFriendly(balance.balance)} {libraCurrency.sign}
          </Text>
          <Text>
            {t("price")} {fiatCurrency.sign}
            {fiatToHumanFriendly(price)} {fiatCurrency.symbol}
          </Text>
        </View>
      )}
    </ThemeConsumer>
  );
}

export default CurrencyBalance;
