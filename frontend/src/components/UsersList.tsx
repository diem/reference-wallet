// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useState } from "react";
import { Button, ListGroup, ListGroupItem } from "reactstrap";

import { RegistrationStatus, User } from "../interfaces/user";
import { useTranslation } from "react-i18next";
import ConfirmationModal from "./ConfirmationModal";

type UserStatus = RegistrationStatus | "Blocked";

interface UserListItemProps {
  user: User;
  status: UserStatus;
  onBlock: (user: User) => void;
}

interface UserListProps {
  users: User[];
  onBlock: (id: number) => void;
}

const STATUS_COLORS = {
  Registered: "warning",
  Pending: "warning",
  Verified: "warning",
  Approved: "secondary",
  Rejected: "danger",
  Blocked: "danger",
};

function UserStatusIcon({ status }: { status: UserStatus }) {
  const statusIcon = status === "Blocked" ? "fa fa-ban" : "fa fa-user-circle";
  return <i className={`${statusIcon} text-${STATUS_COLORS[status]}`} title={status} />;
}

function BlockButton({ isBlocked, onBlock }: { isBlocked: boolean; onBlock: () => void }) {
  const { t } = useTranslation("admin");

  if (isBlocked) {
    return (
      <Button outline size="sm" title="Blocked user" disabled>
        <i className="fa fa-ban" /> {t("users.blocked")}
      </Button>
    );
  } else {
    return (
      <Button outline size="sm" title="Block this user" onClick={onBlock}>
        <i className="fa fa-ban" /> {t("users.block")}
      </Button>
    );
  }
}

function UserListItem({ user, status, onBlock }: UserListItemProps) {
  return (
    <ListGroupItem key={user.id} className="justify-content-between">
      <div className="d-flex">
        {/* Left side container */}
        <span className="text-black mr-4 overflow-auto">
          <div className="d-flex">
            <strong className="text-capitalize">
              <UserStatusIcon status={status} /> {user.first_name} {user.last_name}
            </strong>
          </div>
          <div className="d-flex">
            <span className="small">{user.username}</span>
          </div>
        </span>

        {/* Right side container */}
        <span className="ml-auto text-nowrap">
          <BlockButton isBlocked={status === "Blocked"} onBlock={() => onBlock(user)} />
        </span>
      </div>
    </ListGroupItem>
  );
}

export default function UsersList({ users, onBlock }: UserListProps) {
  const { t } = useTranslation("admin");

  const [blockedUser, setBlockedUser] = useState<User>();

  const confirmBlock = (user: User) => {
    setBlockedUser(user);
  };

  const onCloseConfirmation = async (confirmed: boolean) => {
    if (confirmed) {
      onBlock(blockedUser!.id);
    }
    setBlockedUser(undefined);
  };

  return (
    <>
      <ListGroup>
        {users
          .sort((a, b) => {
            if (a.last_name === b.last_name) {
              if (a.first_name === b.first_name) {
                return a.username > b.username ? 1 : -1;
              }
              return a.first_name > b.first_name ? 1 : -1;
            } else {
              return a.last_name > b.last_name ? 1 : -1;
            }
          })
          .map((user) => (
            <UserListItem
              user={user}
              status={user.is_blocked ? "Blocked" : user.registration_status}
              onBlock={confirmBlock}
            />
          ))}
      </ListGroup>
      <ConfirmationModal
        title={
          <>
            {t("confirmation.title")}{" "}
            <i>{`${blockedUser?.first_name} ${blockedUser?.last_name}`}</i> ?
          </>
        }
        bodyText={t("confirmation.body_text")}
        cancelText={t("confirmation.no")}
        confirmText={t("confirmation.yes")}
        onClose={onCloseConfirmation}
        isOpen={!!blockedUser}
      />
    </>
  );
}
