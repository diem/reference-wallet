// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { TouchableOpacity, View } from "react-native";
import { ListItem, Text, ThemeConsumer } from "react-native-elements";
import { appTheme } from "../styles";
import { useTranslation } from "react-i18next";
import { NewPaymentMethod, PaymentMethod, PaymentMethodProviders, User } from "../interfaces/user";
import { Navigation, NavigationComponentProps } from "react-native-navigation";

type GroupedPaymentMethods = { [key in PaymentMethodProviders]?: PaymentMethod[] };

interface PaymentMethodsFormProps {
  user: User;
  paymentMethods: PaymentMethod[];
  onAdd: (paymentMethod: NewPaymentMethod) => void;
}

function PaymentMethodsForm({
  user,
  componentId,
  paymentMethods,
  onAdd,
}: PaymentMethodsFormProps & NavigationComponentProps) {
  const { t } = useTranslation("settings");

  const { CreditCard, BankAccount } = paymentMethods.reduce(
    (groups, item) => ({
      ...groups,
      [item.provider]: [...(groups[item.provider] || []), item],
    }),
    {} as GroupedPaymentMethods
  );

  return (
    <ThemeConsumer<typeof appTheme>>
      {({ theme }) => (
        <>
          <View style={theme.Section}>
            <Text style={theme.SubTitle}>{t("payment_methods.title")}</Text>
          </View>

          <View style={theme.Section}>
            <Text style={{ fontWeight: "bold", color: "#000000", marginBottom: 16 }}>
              {t("payment_methods.credit_cards.title")}
            </Text>
            {CreditCard?.map((paymentMethod) => (
              <ListItem topDivider={true} key={paymentMethod.id} title={paymentMethod.name} />
            ))}
            <ListItem
              topDivider={true}
              title={
                <TouchableOpacity
                  style={{ alignItems: "center" }}
                  onPress={() => {
                    Navigation.push(componentId, {
                      component: {
                        name: "AddCreditCard",
                        passProps: {
                          user,
                          onSubmit: onAdd,
                        },
                      },
                    });
                  }}
                >
                  <Text style={{ color: "#000000" }}>{t("payment_methods.credit_cards.add")}</Text>
                </TouchableOpacity>
              }
            />
          </View>

          <View style={theme.Section}>
            <Text style={{ fontWeight: "bold", color: "#000000", marginBottom: 16 }}>
              {t("payment_methods.bank_accounts.title")}
            </Text>
            {BankAccount?.map((paymentMethod) => (
              <ListItem topDivider={true} key={paymentMethod.id} title={paymentMethod.name} />
            ))}
            <ListItem
              topDivider={true}
              title={
                <TouchableOpacity
                  style={{ alignItems: "center" }}
                  onPress={() => {
                    Navigation.push(componentId, {
                      component: {
                        name: "AddBankAccount",
                        passProps: {
                          user,
                          onSubmit: onAdd,
                        },
                      },
                    });
                  }}
                >
                  <Text style={{ color: "#000000" }}>{t("payment_methods.bank_accounts.add")}</Text>
                </TouchableOpacity>
              }
            />
          </View>
        </>
      )}
    </ThemeConsumer>
  );
}

export default PaymentMethodsForm;
