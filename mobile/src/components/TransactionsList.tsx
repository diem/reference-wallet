// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Badge, BadgeProps, ListItem, Text } from "react-native-elements";
import { Transaction, TransactionStatus } from "../interfaces/transaction";
import { FiatCurrency, Rates } from "../interfaces/currencies";
import { View } from "react-native";
import { fiatCurrencies, diemCurrencies } from "../currencies";
import { fiatToHumanFriendly, diemToFloat, diemToHumanFriendly } from "../utils/amount-precision";
import { useTranslation } from "react-i18next";
import { shortenDiemAddress } from "../utils/shorten-address";

const STATUS_COLORS: { [key in TransactionStatus]: BadgeProps["status"] } = {
  completed: "success",
  pending: "warning",
  canceled: "error",
};

interface TransactionsListProps {
  transactions: Transaction[];
  fiatCurrencyCode: FiatCurrency;
  rates: Rates;
  onSelect?: (transaction: Transaction) => void;
  bottom?: React.ReactElement;
}

function TransactionsList({
  transactions,
  fiatCurrencyCode,
  rates,
  onSelect,
  bottom,
}: TransactionsListProps) {
  const { t } = useTranslation("transaction");

  const TXExternalReceived = ({ transaction }: { transaction: Transaction }) => (
    <Text style={{ color: "#000000" }}>
      <Text style={{ fontWeight: "bold", color: "#000000" }}>{t("received")}</Text> {t("from")}{" "}
      {shortenDiemAddress(transaction.source.full_addr)}
    </Text>
  );

  const TXExternalSent = ({ transaction }: { transaction: Transaction }) => (
    <Text style={{ color: "#000000" }}>
      <Text style={{ fontWeight: "bold", color: "#000000" }}>{t("sent")}</Text> {t("to")}{" "}
      {shortenDiemAddress(transaction.destination.full_addr)}
    </Text>
  );

  const TXInternalReceived = ({ transaction }: { transaction: Transaction }) => (
    <Text style={{ color: "#000000" }}>
      <Text style={{ fontWeight: "bold", color: "#000000" }}>{t("received")}</Text> {t("from")}{" "}
      {shortenDiemAddress(transaction.source.full_addr)}
    </Text>
  );

  const TXInternalSent = ({ transaction }: { transaction: Transaction }) => (
    <Text style={{ color: "#000000" }}>
      <Text style={{ fontWeight: "bold", color: "#000000" }}>{t("sent")}</Text> {t("to")}{" "}
      {shortenDiemAddress(transaction.destination.full_addr)}
    </Text>
  );

  const TXUnknown = () => <Text style={{ color: "red" }}>Unknown</Text>;

  const TXMeta = ({ transaction }: { transaction: Transaction }) => (
    <View style={{ flexDirection: "row", alignItems: "center" }}>
      <Badge status={STATUS_COLORS[transaction.status]} />
      <Text style={{ fontSize: 14 }}> {new Date(transaction.timestamp).toLocaleDateString()}</Text>
    </View>
  );

  const TXAmount = ({ transaction }: { transaction: Transaction }) => {
    const diemCurrency = diemCurrencies[transaction.currency];
    return (
      <Text style={{ color: "#000000" }}>
        {transaction.direction === "received" ? "+" : "-"}{" "}
        {diemToHumanFriendly(transaction.amount, true)} {diemCurrency.sign}
      </Text>
    );
  };

  const TXPrice = ({ transaction }: { transaction: Transaction }) => {
    const fiatCurrency = fiatCurrencies[fiatCurrencyCode];
    const exchangeRate = rates[transaction.currency][fiatCurrencyCode];

    const price = diemToFloat(transaction.amount) * exchangeRate;

    return (
      <Text style={{ fontSize: 14 }}>
        {fiatCurrency.sign}
        {fiatToHumanFriendly(price, true)} {fiatCurrency.symbol}
      </Text>
    );
  };

  return (
    <>
      {transactions.map((transaction, i) => {
        let direction: any;
        if (transaction.direction === "received" && !!transaction.blockchain_tx) {
          direction = <TXExternalReceived transaction={transaction} />;
        } else if (transaction.direction == "sent" && transaction.blockchain_tx) {
          direction = <TXExternalSent transaction={transaction} />;
        } else if (transaction.direction == "received" && !transaction.blockchain_tx) {
          direction = <TXInternalReceived transaction={transaction} />;
        } else if (transaction.direction == "sent" && !transaction.blockchain_tx) {
          direction = <TXInternalSent transaction={transaction} />;
        } else {
          direction = <TXUnknown />;
        }
        return (
          <ListItem
            key={i}
            onPress={() => onSelect && onSelect(transaction)}
            bottomDivider={true}
            title={direction}
            subtitle={<TXMeta transaction={transaction} />}
            rightTitle={<TXAmount transaction={transaction} />}
            rightSubtitle={<TXPrice transaction={transaction} />}
          />
        );
      })}
      {bottom && <ListItem title={bottom} />}
    </>
  );
}

export default TransactionsList;
