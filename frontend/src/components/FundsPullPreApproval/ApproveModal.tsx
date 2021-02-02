import React from "react";
import { Button, Modal, ModalBody } from "reactstrap";
import CloseButton from "../CloseButton";
import { Approval } from "../../interfaces/approval";
import ApprovalDetails from "./ApprovalDetails";
interface ApproveModalProps {
  approval: Approval | undefined;
  open: boolean;
  onClose: () => void;
}

function ApproveModal({ approval, open, onClose }: ApproveModalProps) {
  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onClose}>
      <ModalBody>
        <CloseButton onClick={onClose} />
        <>
          <h3>Approve Request</h3>
          <ApprovalDetails approval={approval} />
          <span>
            <Button outline onClick={onClose}>
              Cancel
            </Button>
            <Button outline>Approve</Button>
          </span>
        </>
      </ModalBody>
    </Modal>
  );
}

export default ApproveModal;
