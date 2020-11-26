// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import { fiatToHumanFriendly, libraToFloat, libraToHumanFriendly } from "../utils/amount-precision";
import { LibraCurrencyBalance } from "../interfaces/account";
import { fiatCurrencies, libraCurrencies } from "../currencies";
import { ListItem } from "react-native-elements";
import React from "react";
import { FiatCurrency, LibraCurrency, Rates } from "../interfaces/currencies";

interface BalancesListProps {
  balances: LibraCurrencyBalance[];
  fiatCurrencyCode: FiatCurrency;
  rates: Rates;
  onSelect?: (currency: LibraCurrency) => void;
}

function BalancesList({ balances, fiatCurrencyCode, rates, onSelect }: BalancesListProps) {
  const sortedBalances = balances.sort((a, b) => {
    const exchangeRateA = rates[a.currency][fiatCurrencyCode];
    const priceA = libraToFloat(a.balance) * exchangeRateA;
    const exchangeRateB = rates[b.currency][fiatCurrencyCode];
    const priceB = libraToFloat(b.balance) * exchangeRateB;

    return priceA <= priceB ? 1 : -1;
  });

  return (
    <>
      {sortedBalances.map((currencyBalance, i) => {
        const libraCurrency = libraCurrencies[currencyBalance.currency];
        const fiatCurrency = fiatCurrencies[fiatCurrencyCode];
        const exchangeRate = rates[currencyBalance.currency][fiatCurrencyCode];

        const price = libraToFloat(currencyBalance.balance) * exchangeRate;

        return (
          <ListItem
            key={i}
            onPress={() => onSelect && onSelect(currencyBalance.currency)}
            bottomDivider={true}
            title={libraCurrency.name}
            titleStyle={{ fontWeight: "bold", color: "#000000" }}
            rightTitle={`${libraToHumanFriendly(currencyBalance.balance, true)} ${
              libraCurrency.sign
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
