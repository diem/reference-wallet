import React from "react";
import { Modal, ModalBody } from "reactstrap";

interface ApproveModalProps {
  open: boolean;
  onClose: () => void;
}

function ApproveModal({ open, onClose }: ApproveModalProps) {
  function onModalClose() {
    onClose();
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onModalClose}>
      <ModalBody></ModalBody>
    </Modal>
  );
}

export default ApproveModal;
