// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useReducer } from "react";
import { Currency } from "../../interfaces/currencies";
import { settingsContext } from "../../contexts/app";
import WithdrawReview from "./WithdrawReview";
import WithdrawForm from "./WithdrawForm";
import { WithdrawData } from "./interfaces";
import { Quote } from "../../interfaces/cico";
import BackendClient from "../../services/backendClient";
import ErrorMessage from "../Messages/ErrorMessage";
import { diemAmountFromFloat } from "../../utils/amount-precision";
import { BackendError } from "../../services/errors";
import SuccessMessage from "../Messages/SuccessMessage";
import { useTranslation } from "react-i18next";

type WithdrawPhase = "collect" | "quote" | "review" | "execute" | "executing" | "done";

interface State {
  phase: WithdrawPhase;
  requestData: WithdrawData;
  quote?: Quote;
  errorMessage?: string;
}

type Action =
  | { type: "collect" }
  | { type: "quote"; requestData: WithdrawData }
  | { type: "review"; quote: Quote }
  | { type: "execute" }
  | { type: "executing" }
  | { type: "done" }
  | { type: "error"; errorMessage: string };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "collect":
      return { ...state, phase: "collect" };
    case "quote":
      return { phase: "quote", requestData: action.requestData };
    case "review":
      return { ...state, phase: "review", quote: action.quote };
    case "execute":
      return { ...state, phase: "execute" };
    case "executing":
      return { ...state, phase: "executing" };
    case "done":
      return { ...state, phase: "done" };
    case "error":
      let phase = state.phase;
      if (state.phase === "quote") {
        phase = "collect";
      } else if (state.phase === "execute") {
        phase = "review";
      }
      return { ...state, phase, errorMessage: action.errorMessage };
  }
}

interface WithdrawProps {
  initialCurrency?: Currency;
  onComplete: () => void;
}

function Withdraw({ initialCurrency, onComplete }: WithdrawProps) {
  const { t } = useTranslation("transfer");
  const [settings] = useContext(settingsContext)!;

  const [{ phase, requestData, quote, errorMessage }, dispatch] = useReducer(reducer, {
    phase: "collect",
    requestData: {
      currency: initialCurrency,
      fiatCurrency: settings.defaultFiatCurrencyCode!,
    },
  });

  const showReview = ["review", "execute", "executing", "done"].includes(phase);

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

  useEffect(() => {
    let isOutdated = false;

    const requestQuote = async () => {
      try {
        const newQuote = await new BackendClient().requestWithdrawQuote(
          requestData.currency!,
          requestData.fiatCurrency,
          diemAmountFromFloat(requestData.amount!)
        );
        if (!isOutdated) {
          dispatch({ type: "review", quote: newQuote });
        }
      } catch (e) {
        if (e instanceof BackendError) {
          dispatch({ type: "error", errorMessage: e.message });
        } else {
          dispatch({ type: "error", errorMessage: "Internal Error" });
          console.error("Unexpected error", e);
        }
      }
    };

    const executeQuote = async () => {
      try {
        dispatch({ type: "executing" });
        await new BackendClient().executeQuote(quote!.quoteId, requestData.fundingSource!);
        dispatch({ type: "done" });
      } catch (e) {
        if (e instanceof BackendError) {
          dispatch({ type: "error", errorMessage: e.message });
        } else {
          dispatch({ type: "error", errorMessage: "Internal Error" });
          console.error("Unexpected error", e);
        }
      }
    };

    if (phase === "quote") {
      // noinspection JSIgnoredPromiseFromCall
      requestQuote();
    } else if (phase === "execute") {
      // noinspection JSIgnoredPromiseFromCall
      executeQuote();
    }

    return () => {
      isOutdated = true;
    };
  }, [phase, requestData, quote]);

  if (!settings.user || !settings.account) {
    return null;
  }

  return (
    <>
      {errorMessage && <ErrorMessage message={errorMessage} />}
      {phase === "done" && <SuccessMessage message={t("withdraw.success_message")} />}

      {showReview ? (
        <WithdrawReview
          quote={quote!}
          fundingSourceId={requestData.fundingSource!}
          submitting={phase === "executing"}
          submitted={phase === "done"}
          onBack={() => dispatch({ type: "collect" })}
          onConfirm={() => dispatch({ type: "execute" })}
          onComplete={onComplete}
        />
      ) : (
        <WithdrawForm
          value={requestData}
          onSubmit={(newData) => dispatch({ type: "quote", requestData: newData })}
        />
      )}
    </>
  );
}

export default Withdraw;
