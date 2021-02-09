import { Approval } from "../../interfaces/approval";
import React from "react";
import { Button, Col, Row } from "reactstrap";
import ApprovalDetails from "./ApprovalDetails";

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
  return (
    <li className="list-group-item">
      <Row>
        <Col sm="8" className="p-0">
          <ApprovalDetails approval={approval} />
        </Col>
        {!disableApproveRejectButtons && (
          <Col sm="4" className="p-0 d-flex align-items-end">
            <div className="mt-5 ml-auto">
              <Button
                className="mr-1"
                color="black"
                outline
                size="sm"
                disabled={!onRejectClick}
                onClick={onRejectClick}
              >
                <i className="fa fa-times mr-1" />
                Reject
              </Button>
              <Button color="black" size="sm" disabled={!onApproveClick} onClick={onApproveClick}>
                <i className="fa fa-check mr-1" />
                Approve
              </Button>
            </div>
          </Col>
        )}
        {!disableRevokeButton && (
          <Col sm="4" className="p-0 d-flex align-items-end">
            <div className="mt-5 ml-auto">
              <a href="#" onClick={onRevokeClick} aria-disabled={!onRevokeClick}>
                Revoke this request
              </a>
              {/*<Button*/}
              {/*  className="btn-link"*/}
              {/*  outline*/}
              {/*  onClick={onRevokeClick}*/}
              {/*  disabled={!onRevokeClick}*/}
              {/*>*/}
              {/*  Revoke this request*/}
              {/*</Button>*/}
            </div>
          </Col>
        )}
      </Row>
    </li>
  );
}

export default FundsPullPreApproval;
