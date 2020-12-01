// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext, useEffect, useState } from "react";
import { Button, Container } from "reactstrap";
import Breadcrumbs from "../../components/Breadcrumbs";
import BackendClient from "../../services/backendClient";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import SettlementDetails from "../../components/SettlementDetails";
import { Debt } from "../../interfaces/settlement";
import { settingsContext } from "../../contexts/app";
import { useTranslation } from "react-i18next";

export default function Liquidity() {
  const { t } = useTranslation("admin");
  const [settings] = useContext(settingsContext)!;
  const [debt, setDebt] = useState<Debt[]>([]);

  // Loads the settlement details
  useEffect(() => {
    let isOutdated = false;

    const fetchSettlement = async () => {
      try {
        const settlementDebt = await new BackendClient().getPendingSettlement();

        if (!isOutdated) {
          setDebt(settlementDebt);
        }
      } catch (e) {
        console.error("Unexpected error", e);
      }
    };

    // noinspection JSIgnoredPromiseFromCall
    fetchSettlement();

    return () => {
      isOutdated = true;
    };
  }, []);

  // Refreshes the authentication token
  useEffect(() => {
    try {
      // noinspection JSIgnoredPromiseFromCall
      new BackendClient().refreshUser();
    } catch (e) {
      console.error(e);
    }
  }, []);

  const settle = async () => {
    try {
      const confirmation = `Payment approved by ${settings.user?.first_name} ${settings.user?.last_name}`;

      const backend = new BackendClient();
      await backend.settleDebts(
        debt.map((d) => d.debt_id),
        confirmation
      );
      const settlementDebt = await backend.getPendingSettlement();

      setDebt(settlementDebt);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      <Breadcrumbs pageName="Liquidity" />
      <Container className="py-5">
        <h1 className="h3 text-center">{t("liquidity.title")}</h1>

        <section className="my-5">
          {debt.length === 0 && <ErrorMessage message={t("notifications.no_debt")} />}
          <SettlementDetails debt={debt} />
          <div className="my-3 d-flex justify-content-around">
            <Button onClick={settle} color="black" outline>
              <i className="fa fa-user-plus" /> {t("liquidity.settle")}
            </Button>
          </div>
        </section>
      </Container>
    </>
  );
}
