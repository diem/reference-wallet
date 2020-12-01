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
import SelectDropdown from "../components/Select";
import { NewPaymentMethod, User } from "../interfaces/user";

const BANKS = ["My Bank LTD", "My Other Bank"];

interface BankAccount {
  bank: keyof typeof BANKS;
  name: string;
  accountNumber: number;
}

interface AddBankAccountProps {
  user: User;
  onSubmit: (paymentMethod: NewPaymentMethod) => void;
}

function AddBankAccount({
  user,
  onSubmit,
  componentId,
}: AddBankAccountProps & NavigationComponentProps) {
  const { t } = useTranslation("settings");

  const [bankAccount, setBankAccount] = useState<BankAccount>({
    bank: 0,
    name: `${user.first_name} ${user.last_name}`,
    accountNumber: 123456789,
  });

  function onFormSubmit() {
    const bank = BANKS[bankAccount.bank];
    const last4digits = bankAccount.accountNumber.toString().slice(-4);

    onSubmit({
      name: `${bankAccount.name} ${bank} (**** ${last4digits})`,
      provider: "BankAccount",
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
              <Text>{t("payment_methods.bank_accounts.form.account_number")}</Text>
              <Input renderErrorMessage={false} value={bankAccount.accountNumber.toString()} />
            </View>

            <View style={theme.Section}>
              <Text>{t("payment_methods.bank_accounts.form.bank")}</Text>
              <SelectDropdown options={BANKS} value={bankAccount.bank} />
            </View>

            <View style={theme.Section}>
              <Text>{t("payment_methods.bank_accounts.form.name")}</Text>
              <Input renderErrorMessage={false} value={bankAccount.name} />
            </View>

            <Button title={t("payment_methods.bank_accounts.form.submit")} onPress={onFormSubmit} />
          </View>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default AddBankAccount;
