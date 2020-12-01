// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { View } from "react-native";
import { Navigation, NavigationComponentProps } from "react-native-navigation";
import { Button, ThemeConsumer, Text } from "react-native-elements";
import { useTranslation } from "react-i18next";
import faker from "faker";
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
import moment from "moment";

type SubmitStatuses = "edit" | "sending" | "fail" | "success";

function Verify({ componentId }: NavigationComponentProps) {
  const { t } = useTranslation("verify");

  const [step, setStep] = useState<number>(1);
  const [errorMessage, setErrorMessage] = useState<string>();
  const [submitStatus, setSubmitStatus] = useState<SubmitStatuses>("edit");
  const [dummyUserInformation, setDummyUserInformation] = useState<UserInfo[]>();

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

  useEffect(() => {
    setDummyUserInformation(
      [1, 2, 3].map(() => {
        return {
          ...userInformation,
          first_name: faker.name.firstName(),
          last_name: faker.name.lastName(),
          dob: moment(faker.date.past()),
          phone: "1 " + faker.phone.phoneNumberFormat(),
          country: faker.address.countryCode(),
          state: faker.address.state(),
          city: faker.address.city(),
          address_1: faker.address.streetAddress(),
          address_2: "",
          zip: faker.address.zipCode(),
        };
      })
    );
  }, []);

  return (
    <ScreenLayout hideHeaderBack={true} componentId={componentId}>
      <ThemeConsumer<typeof appTheme>>
        {({ theme }) => (
          <>
            <ExampleSectionWarning />
            <View style={theme.Container}>
              {errorMessage && <ErrorMessage message={errorMessage} />}

              {step === 1 && dummyUserInformation && (
                <View style={theme.Section}>
                  <Text h1>{t("choose_dummy_identity")}</Text>
                  {dummyUserInformation.map((dummyInfo, i) => (
                    <Button
                      key={i}
                      type="outline"
                      title={`${dummyInfo.first_name} ${dummyInfo.last_name} (${dummyInfo.country})`}
                      onPress={() => setUserInformation(dummyInfo)}
                    />
                  ))}
                </View>
              )}

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
            </View>
          </>
        )}
      </ThemeConsumer>
    </ScreenLayout>
  );
}

export default withUserContext(Verify);
