// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { fiatToHumanFriendly, diemToFloat, diemToHumanFriendly } from "../utils/amount-precision";
import { DiemCurrencyBalance } from "../interfaces/account";
import { fiatCurrencies, diemCurrencies } from "../currencies";
import { ListItem } from "react-native-elements";
import React from "react";
import { FiatCurrency, DiemCurrency, Rates } from "../interfaces/currencies";

interface BalancesListProps {
  balances: DiemCurrencyBalance[];
  fiatCurrencyCode: FiatCurrency;
  rates: Rates;
  onSelect?: (currency: DiemCurrency) => void;
}

function BalancesList({ balances, fiatCurrencyCode, rates, onSelect }: BalancesListProps) {
  const sortedBalances = balances.sort((a, b) => {
    const exchangeRateA = rates[a.currency][fiatCurrencyCode];
    const priceA = diemToFloat(a.balance) * exchangeRateA;
    const exchangeRateB = rates[b.currency][fiatCurrencyCode];
    const priceB = diemToFloat(b.balance) * exchangeRateB;

    return priceA <= priceB ? 1 : -1;
  });

  return (
    <>
      {sortedBalances.map((currencyBalance, i) => {
        const diemCurrency = diemCurrencies[currencyBalance.currency];
        const fiatCurrency = fiatCurrencies[fiatCurrencyCode];
        const exchangeRate = rates[currencyBalance.currency][fiatCurrencyCode];

        const price = diemToFloat(currencyBalance.balance) * exchangeRate;

        return (
          <ListItem
            key={i}
            onPress={() => onSelect && onSelect(currencyBalance.currency)}
            bottomDivider={true}
            title={diemCurrency.name}
            titleStyle={{ fontWeight: "bold", color: "#000000" }}
            rightTitle={`${diemToHumanFriendly(currencyBalance.balance, true)} ${
              diemCurrency.sign
            }`}
            rightTitleStyle={{ color: "#000000" }}
            rightSubtitle={`${fiatCurrency.sign}${fiatToHumanFriendly(price, true)} ${
              fiatCurrency.symbol
            }`}
          />
        );
      })}
    </>
  );
}

export default BalancesList;
