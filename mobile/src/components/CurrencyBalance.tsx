// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from "react-i18next";
import React from "react";
import { DiemCurrencyBalance } from "../interfaces/account";
import { Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";
import { View } from "react-native";
import { FiatCurrency, Rates } from "../interfaces/currencies";
import { fiatToHumanFriendly, diemToFloat, diemToHumanFriendly } from "../utils/amount-precision";
import { fiatCurrencies, diemCurrencies } from "../currencies";

interface TotalBalanceProps {
  balance: DiemCurrencyBalance;
  fiatCurrencyCode: FiatCurrency;
  rates: Rates;
}

function CurrencyBalance({ balance, fiatCurrencyCode, rates }: TotalBalanceProps) {
  const { t } = useTranslation("layout");

  const diemCurrency = diemCurrencies[balance.currency];
  const fiatCurrency = fiatCurrencies[fiatCurrencyCode];

  const exchangeRate = rates[balance.currency][fiatCurrencyCode];
  const price = diemToFloat(balance.balance) * exchangeRate;

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <View style={{ ...theme.Section, alignItems: "center" }}>
          <Text style={theme.Title}>
            {diemToHumanFriendly(balance.balance)} {diemCurrency.sign}
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
