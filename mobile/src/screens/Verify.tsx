// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, ThemeConsumer } from "react-native-elements";
import { useTranslation } from "react-i18next";
import { UserInfo } from "../interfaces/user";
import { appTheme } from "../styles";
import { withUserContext } from "../contexts/user";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import SessionStorage from "../services/sessionStorage";
import Step1Identity from "./VerifySteps/Step1Identity";
import Step2Country from "./VerifySteps/Step2Country";
import Step3Address from "./VerifySteps/Step3Address";
import Step4Document from "./VerifySteps/Step4Document";
import Step5DefaultCurrency from "./VerifySteps/Step5DefaultCurrency";
import ScreenLayout from "../components/ScreenLayout";
import ErrorMessage from "../components/Messages/ErrorMessage";
import ExampleSectionWarning from "../components/ExampleSectionWarning";

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function Verify({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("verify");

  const [step, setStep] = useState<number>(1);
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");

  const [userInformation, setUserInformation] = useState<UserInfo>({
    selected_fiat_currency: "USD",
    selected_language: "en",
    first_name: "",
    last_name: "",
    dob: "",
    phone: "1 ", // USA country code
    country: undefined,
    state: "",
    city: "",
    address_1: "",
    address_2: "",
    zip: "",
  });

  const nextStep = () => {
    setStep(step + 1);
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  async function submit(userInfo: UserInfo) {
    try {
      setErrorMessage(undefined);
      setSubmitStatus("sending");
      const token = await SessionStorage.getAccessToken();
      await new BackendClient(token).updateUserInfo(userInfo);
      await Navigation.setStackRoot(componentId, {
        component: {
          name: "Home",
        },
      });
      setSubmitStatus("success");
    } catch (e) {
      setSubmitStatus("fail");
      if (e instanceof BackendError) {
        setErrorMessage(e.message);
      } else {
        setErrorMessage("Internal Error");
        console.error("Unexpected error", e);
      }
    }
  }

  const setSherlockUserInfo = () => {
    setUserInformation({
      ...userInformation,
      first_name: userInformation.first_name.length ? userInformation.first_name : "Sherlock",
      last_name: userInformation.last_name.length ? userInformation.last_name : "Holmes",
      // dob: moment("1861-06-01"),
      dob: "1861-06-01",
      phone: "44 2079460869",
      country: "GB",
      state: "",
      city: "London",
      address_1: "221B Baker Street",
      address_2: "",
      zip: "NW1 6XE",
    });
  };

  return (
    <ScreenLayout componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            <ExampleSectionWarning />
            <View style={theme.Container}>
              {errorMessage && <ErrorMessage message={errorMessage} />}

              {step === 1 && (
                <Step1Identity
                  info={userInformation}
                  onSubmit={(info) => {
                    setUserInformation({ ...userInformation, ...info });
                    nextStep();
                  }}
                />
              )}
              {step === 2 && (
                <Step2Country
                  info={userInformation}
                  onBack={prevStep}
                  onSubmit={(info) => {
                    setUserInformation({ ...userInformation, ...info });
                    nextStep();
                  }}
                />
              )}
              {step === 3 && (
                <Step3Address
                  info={userInformation}
                  onBack={prevStep}
                  onSubmit={(info) => {
                    setUserInformation({ ...userInformation, ...info });
                    nextStep();
                  }}
                />
              )}
              {step === 4 && (
                <Step4Document
                  info={userInformation}
                  onBack={prevStep}
                  onSubmit={() => {
                    nextStep();
                  }}
                />
              )}
              {step === 5 && (
                <Step5DefaultCurrency
                  info={userInformation}
                  onBack={prevStep}
                  onSubmit={(info) => {
                    setUserInformation({ ...userInformation, ...info });
                    submit(info);
                  }}
                />
              )}

              {(step === 1 || step === 2 || step === 3) && (
                <Button type="outline" title={t("fill_sherlock")} onPress={setSherlockUserInfo} />
              )}
            </View>
          </>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withUserContext(Verify);
