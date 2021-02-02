//RejectModal
import React from "react";
import { Modal, ModalBody } from "reactstrap";

interface RejectModalProps {
  open: boolean;
  onClose: () => void;
}

function RejectModal({ open, onClose }: RejectModalProps) {
  function onModalClose() {
    onClose();
  }

  return (
    <Modal className="modal-dialog-centered" isOpen={open} onClosed={onModalClose}>
      <ModalBody></ModalBody>
    </Modal>
  );
}

export default RejectModal;
