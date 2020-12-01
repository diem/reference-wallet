// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import moment from "moment";
import { Button, Container } from "reactstrap";
import { Redirect } from "react-router-dom";
import { useTranslation } from "react-i18next";
import faker from "faker";
import { countries } from "countries-list";
import { settingsContext } from "../contexts/app";
import BackendClient from "../services/backendClient";
import { BackendError } from "../services/errors";
import { UserInfo } from "../interfaces/user";
import Step1Identity from "./VerifySteps/Step1Identity";
import Step2Country from "./VerifySteps/Step2Country";
import Step3Address from "./VerifySteps/Step3Address";
import Step4Document from "./VerifySteps/Step4Document";
import Step5DefaultCurrency from "./VerifySteps/Step5DefaultCurrency";
import ExampleSectionWarning from "../components/ExampleSectionWarning";
import ErrorMessage from "../components/Messages/ErrorMessage";
import VerifyLoader from "../components/VerifyLoader";

const Verify = () => {
  const { t } = useTranslation("verify");
  const [settings, setSettings] = useContext(settingsContext)!;
  const user = settings.user;

  const [step, setStep] = useState<number>(1);
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
  const [dummyUserInformation, setDummyUserInformation] = useState<UserInfo[]>();
  const [documentFile, setDocumentFile] = useState<File | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const [submitStatus, setSubmitStatus] = useState<"edit" | "sending" | "fail" | "success">("edit");

  useEffect(() => {
    async function refreshUser() {
      try {
        await new BackendClient().refreshUser();
      } catch (e) {
        console.error(e);
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    refreshUser();
  }, []);

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
      const user = await new BackendClient().updateUserInfo(userInfo);
      setSettings({ ...settings, user });
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
        const countryCode = "US";
        return {
          ...userInformation,
          first_name: faker.name.firstName(),
          last_name: faker.name.lastName(),
          dob: moment(faker.date.past()),
          phone: countries[countryCode].phone + " " + faker.phone.phoneNumberFormat(),
          country: countryCode,
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
    <>
      {submitStatus === "success" && <Redirect to="/" />}
      <ExampleSectionWarning />
      <Container className="py-5 d-flex flex-column">
        {user && (
          <section className="slim-section m-auto">
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
                onSubmit={(file) => {
                  setDocumentFile(file);
                  nextStep();
                }}
              />
            )}
            {step === 5 && (
              <Step5DefaultCurrency
                info={userInformation}
                onBack={prevStep}
                onContinue={(info) => {
                  setUserInformation({ ...userInformation, ...info });
                  submit(info);
                }}
              />
            )}
            {(step === 1 || step === 2 || step === 3) && dummyUserInformation && (
              <>
                <h3 className="h5 mt-4 mb-2">{t("choose_dummy_identity")}</h3>
                {dummyUserInformation.map((dummyInfo, i) => (
                  <Button
                    key={i}
                    size="sm"
                    color="dark"
                    block={true}
                    outline
                    onClick={() => setUserInformation(dummyInfo)}
                  >
                    {dummyInfo.first_name} {dummyInfo.last_name} ({dummyInfo.country})
                  </Button>
                ))}
              </>
            )}
          </section>
        )}
        {!user && <VerifyLoader />}
      </Container>
    </>
  );
};

export default Verify;
