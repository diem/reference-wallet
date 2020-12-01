// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, Input, Text, ThemeConsumer } from "react-native-elements";
import { v4 as uuid4 } from "react-native-uuid";
import ScreenLayout from "../components/ScreenLayout";
import { appTheme } from "../styles";
import { useTranslation } from "react-i18next";
import { NewPaymentMethod, User } from "../interfaces/user";

interface AddCreditCardProps {
  user: User;
  onSubmit: (paymentMethod: NewPaymentMethod) => void;
}

function AddCreditCard({
  user,
  onSubmit,
  componentId,
}: AddCreditCardProps & NavigationComponentProps) {
  const { t } = useTranslation("settings");

  const [creditCard, setCreditCard] = useState({
    number: 4111111111111111,
    name: `${user.first_name} ${user.last_name}`,
    expiry: "12/20",
    cvc: 123,
    focused: undefined,
  });

  function onFormSubmit() {
    const last4digits = creditCard.number.toString().slice(-4);
    onSubmit({
      name: `${creditCard.name} (**** **** **** ${last4digits} ${creditCard.expiry})`,
      provider: "CreditCard",
      token: uuid4(),
    });
    Navigation.pop(componentId);
  }

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <View style={theme.Container}>
            <View style={theme.Section}>
              <Text>{t("payment_methods.credit_cards.form.number")}</Text>
              <Input renderErrorMessage={false} value={creditCard.number.toString()} />
            </View>

            <View style={theme.Section}>
              <Text>{t("payment_methods.credit_cards.form.name")}</Text>
              <Input renderErrorMessage={false} value={creditCard.name} />
            </View>

            <View style={theme.Section}>
              <Text>{t("payment_methods.credit_cards.form.expiry")}</Text>
              <Input renderErrorMessage={false} value={creditCard.expiry} />
            </View>

            <View style={theme.Section}>
              <Text>{t("payment_methods.credit_cards.form.cvc")}</Text>
              <Input renderErrorMessage={false} value={creditCard.cvc.toString()} />
            </View>

            <Button title={t("payment_methods.credit_cards.form.submit")} onPress={onFormSubmit} />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default AddCreditCard;
