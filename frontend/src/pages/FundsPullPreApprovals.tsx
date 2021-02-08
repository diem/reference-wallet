// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { Approval } from "../interfaces/approval";
import BackendClient from "../services/backendClient";
import TestnetWarning from "../components/TestnetWarning";
import Breadcrumbs from "../components/Breadcrumbs";
import { Container } from "reactstrap";
import FundsPullPreApprovalsList from "../components/FundsPullPreApproval/FundsPullPreApprovalsList";

const REFRESH_APPROVALS_INTERVAL = 3000;

function FundsPullPreApprovals() {
  const [newApprovals, setNewApprovals] = useState<Approval[]>([]);
  const [activeApprovals, setActiveApprovals] = useState<Approval[]>([]);
  const [historyApprovals, setHistoryApprovals] = useState<Approval[]>([]);

  let refreshApprovals = true;

  useEffect(() => {
    const fetchApprovals = async () => {
      try {
        if (refreshApprovals) {
          let innerNewApprovals: Approval[] = [];
          let innerActiveApprovals: Approval[] = [];
          let innerHistoryApprovals: Approval[] = [];
          const approvals = await new BackendClient().getAllFundsPullPreApprovals();
          for (const approval of approvals) {
            if (approval.status === "pending") {
              innerNewApprovals.push(approval);
            } else if (approval.status === "valid") {
              const now = new Date().toISOString();
              if (Date.parse(approval!.scope.expiration_timestamp) < Date.parse(now)) {
                innerHistoryApprovals.push(approval);
              } else {
                innerActiveApprovals.push(approval);
              }
            } else {
              innerHistoryApprovals.push(approval);
            }
          }
          setNewApprovals(innerNewApprovals);
          setActiveApprovals(innerActiveApprovals);
          setHistoryApprovals(innerHistoryApprovals);
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
  }, [setNewApprovals, setActiveApprovals, setHistoryApprovals]);

  return (
    <>
      <TestnetWarning />

      <Breadcrumbs pageName={"All Funds Pull Pre Approvals"} />
      <Container className="py-5">
        {!!newApprovals.length && (
          <section>
            <h2 className="pl-1 h5 font-weight-normal text-body">New Requests</h2>
            <FundsPullPreApprovalsList
              approvals={newApprovals}
              displayApproveRejectButtons={true}
              displayRevokeButton={false}
            />
          </section>
        )}
        {!!activeApprovals.length && (
          <section className="pt-4">
            <h2 className="pl-1 h5 font-weight-normal text-body">Active Requests</h2>
            <FundsPullPreApprovalsList
              approvals={activeApprovals}
              displayApproveRejectButtons={false}
              displayRevokeButton={true}
            />
          </section>
        )}
        {!!historyApprovals.length && (
          <section className="pt-4">
            <h2 className="pl-1 h5 font-weight-normal text-body">History</h2>

            <FundsPullPreApprovalsList
              approvals={historyApprovals}
              displayApproveRejectButtons={false}
              displayRevokeButton={false}
            />
          </section>
        )}
      </Container>
    </>
  );
}

export default FundsPullPreApprovals;
