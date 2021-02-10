// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { Approval } from "../interfaces/approval";
import BackendClient from "../services/backendClient";
import TestnetWarning from "../components/TestnetWarning";
import Breadcrumbs from "../components/Breadcrumbs";
import { Container } from "reactstrap";
import FundsPullPreApprovalsList from "../components/FundsPullPreApproval/FundsPullPreApprovalsList";
import { useTranslation } from "react-i18next";

const REFRESH_APPROVALS_INTERVAL = 3000;

function FundsPullPreApprovals() {
  const { t } = useTranslation("funds_pull_pre_approval");
  const [approvals, setApprovals] = useState<Approval[]>([]);

  let refreshApprovals = true;

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        if (refreshApprovals) {
          setApprovals(await new BackendClient().getAllFundsPullPreApprovals());
        }
        setTimeout(fetchApprovals, REFRESH_APPROVALS_INTERVAL);
      } catch (e) {
        console.error(e);
      }
    };

    // noinspection JSIgnoredPromiseFromCall
    fetchApprovals();

    return () => {
      refreshApprovals = false;
    };
  }, [setApprovals]);

  let newApprovals: Approval[] = [];
  let activeApprovals: Approval[] = [];
  let historyApprovals: Approval[] = [];

  for (const approval of approvals) {
    if (approval.status === "pending") {
      newApprovals.push(approval);
    } else if (approval.status === "valid") {
      const expiration_timestamp = new Date(approval.scope.expiration_timestamp * 1000);
      const now = new Date();
      if (expiration_timestamp < now) {
        historyApprovals.push(approval);
      } else {
        activeApprovals.push(approval);
      }
    } else {
      historyApprovals.push(approval);
    }
  }

  return (
    <>
      <TestnetWarning />

      <Breadcrumbs pageName={t("page.title")} />
      <Container className="py-5">
        {!!newApprovals.length && (
          <section>
            <h2 className="pl-1 h5 font-weight-normal text-body">{t("page.new_requests")}</h2>
            <FundsPullPreApprovalsList approvals={newApprovals} disableRevokeButton />
          </section>
        )}
        {!!activeApprovals.length && (
          <section className="pt-4">
            <h2 className="pl-1 h5 font-weight-normal text-body">{t("page.active_requests")}</h2>
            <FundsPullPreApprovalsList approvals={activeApprovals} disableApproveRejectButtons />
          </section>
        )}
        {!!historyApprovals.length && (
          <section className="pt-4">
            <h2 className="pl-1 h5 font-weight-normal text-body">{t("page.history")}</h2>
            <FundsPullPreApprovalsList
              approvals={historyApprovals}
              disableApproveRejectButtons
              disableRevokeButton
            />
          </section>
        )}
        {!approvals.length && (
          <section className="pt-4">
            <h2 className="pl-1 h5 font-weight-normal text-body">{t("page.no_approvals")}</h2>
          </section>
        )}
      </Container>
    </>
  );
}

export default FundsPullPreApprovals;
