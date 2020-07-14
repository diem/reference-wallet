// Copyright (c) The Libra Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import moment from "moment";
import { Button, Container } from "reactstrap";
import { Redirect } from "react-router-dom";
import { useTranslation } from "react-i18next";
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

  const setSherlockUserInfo = () => {
    setUserInformation({
      ...userInformation,
      first_name: userInformation.first_name.length ? userInformation.first_name : "Sherlock",
      last_name: userInformation.last_name.length ? userInformation.last_name : "Holmes",
      dob: moment("1861-06-01"),
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
            {(step === 1 || step === 2 || step === 3) && (
              <Button size="sm" color="dark" className="mt-4" outline onClick={setSherlockUserInfo}>
                {t("fill_sherlock")}
              </Button>
            )}
          </section>
        )}
        {!user && <VerifyLoader />}
      </Container>
    </>
  );
};

export default Verify;
