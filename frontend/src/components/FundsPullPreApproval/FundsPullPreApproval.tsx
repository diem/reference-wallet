import { Approval } from "../../interfaces/approval";
import React from "react";
import { Button, Col, Row } from "reactstrap";
import ApprovalDetails from "./ApprovalDetails";
import { useTranslation } from "react-i18next";

interface ApprovalProps {
  approval: Approval;
  onApproveClick: () => void;
  onRejectClick: () => void;
  onRevokeClick: () => void;
  disableApproveRejectButtons?: boolean;
  disableRevokeButton?: boolean;
}

function FundsPullPreApproval({
  approval,
  onApproveClick,
  onRejectClick,
  onRevokeClick,
  disableApproveRejectButtons,
  disableRevokeButton,
}: ApprovalProps) {
  const { t } = useTranslation("funds_pull_pre_approval");

  return (
    <li className="list-group-item">
      <Row>
        <Col sm="8" className="p-0">
          <div className="ml-2">
            <ApprovalDetails approval={approval} />
          </div>
        </Col>
        {!disableApproveRejectButtons && (
          <Col sm="4" className="p-0 d-flex align-items-end">
            <div className="mt-5 mr-2 ml-auto">
              <Button
                className="mr-1"
                color="black"
                outline
                size="sm"
                disabled={!onRejectClick}
                onClick={onRejectClick}
              >
                <i className="fa fa-times mr-1" />
                {t("reject")}
              </Button>
              <Button color="black" size="sm" disabled={!onApproveClick} onClick={onApproveClick}>
                <i className="fa fa-check mr-1" />
                {t("approve")}
              </Button>
            </div>
          </Col>
        )}
        {!disableRevokeButton && (
          <Col sm="4" className="p-0 d-flex align-items-end">
            <div className="mt-5 mr-2 ml-auto">
              <a href="#" onClick={onRevokeClick} aria-disabled={!onRevokeClick}>
                {t("revoke_link")}
              </a>
            </div>
          </Col>
        )}
      </Row>
    </li>
  );
}

export default FundsPullPreApproval;
