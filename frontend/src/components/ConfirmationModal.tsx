// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React from "react";
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from "reactstrap";

export interface ConfirmationModalProps {
  title: React.ReactNode;
  bodyText: string;
  cancelText: string;
  confirmText: string;
  onClose: (confirmed: boolean) => void;
  isOpen: boolean;
}

export default function ConfirmationModal({
  title,
  bodyText,
  cancelText,
  confirmText,
  onClose,
  isOpen,
}: ConfirmationModalProps) {
  return (
    <Modal centered className="reactstrap-confirm" isOpen={isOpen} toggle={() => onClose(false)}>
      <ModalHeader toggle={() => onClose(false)}>{title}</ModalHeader>
      <ModalBody>{bodyText}</ModalBody>
      <ModalFooter>
        <Button outline color="black" onClick={() => onClose(false)}>
          {cancelText}
        </Button>{" "}
        <Button color="black" onClick={() => onClose(true)}>
          {confirmText}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
