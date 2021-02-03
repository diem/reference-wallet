import { Approval } from "../../interfaces/approval";
import React from "react";
import { classNames } from "../../utils/class-names";
import { Button, Col, Container, Row } from "reactstrap";
import ApprovalDetails from "./ApprovalDetails";

interface ApprovalProps {
  approval: Approval;
  onApproveClick: () => void;
  onRejectClick: () => void;
  onAnyClickSetApproval: () => void;
}

function FundsPullPreApproval({
  approval,
  onApproveClick,
  onRejectClick,
  onAnyClickSetApproval,
}: ApprovalProps) {
  const itemStyles = {
    "list-group-item": true,
  };

  const onAnyClick = (method: () => void) => () => {
    method();
    onAnyClickSetApproval();
  };

  return (
    <li className={classNames(itemStyles)} key={approval.funds_pull_pre_approval_id}>
      <Container>
        <Row>
          <Col sm="8" className="p-0">
            <ApprovalDetails approval={approval} />
          </Col>
          <Col sm="4" className="p-0 d-flex align-items-end">
            <div className="mt-5 ml-auto">
              <Button
                className="mr-1 btn-black"
                size="sm"
                disabled={!onRejectClick}
                onClick={onAnyClick(onRejectClick)}
              >
                <i className="fa fa-times mr-1" />
                Reject
              </Button>
              <Button size="sm" disabled={!onApproveClick} onClick={onAnyClick(onApproveClick)}>
                <i className="fa fa-check mr-1" />
                Approve
              </Button>
            </div>
          </Col>
        </Row>
      </Container>
    </li>
  );
}

export default FundsPullPreApproval;
