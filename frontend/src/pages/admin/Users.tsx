// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { Container } from "reactstrap";
import UsersList from "../../components/UsersList";
import Breadcrumbs from "../../components/Breadcrumbs";
import BackendClient from "../../services/backendClient";
import { User } from "../../interfaces/user";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import { useTranslation } from "react-i18next";

export default function Users() {
  const { t } = useTranslation("admin");
  const [users, setUsers] = useState<User[]>([]);

  // Loads the users
  useEffect(() => {
    let isOutdated = false;

    const fetchUsers = async () => {
      try {
        const fetchedUsers = await new BackendClient().getUsers(false);

        if (!isOutdated) {
          setUsers(fetchedUsers);
        }
      } catch (e) {
        console.error("Unexpected error", e);
      }
    };

    // noinspection JSIgnoredPromiseFromCall
    fetchUsers();

    return () => {
      isOutdated = true;
    };
  }, []);

  // Refreshes the authentication token
  useEffect(() => {
    async function refreshUser() {
      try {
        await new BackendClient().refreshUser();
      } catch (e) {
        console.error(e);
      }
    }
    // noinspection JSIgnoredPromiseFromCall
    refreshUser();
  }, []);

  const blockUser = async (user_id: number) => {
    try {
      await new BackendClient().blockUser(user_id);
      const fetchedUsers = await new BackendClient().getUsers(false);
      setUsers(fetchedUsers);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      <Breadcrumbs pageName="Users" />
      <Container className="py-5">
        <h1 className="h3 text-center">{t("navigation.users")}</h1>

        <section className="my-5">
          {users.length === 0 && <ErrorMessage message={t("notifications.no_users")} />}
          <UsersList users={users} onBlock={blockUser} />
        </section>
      </Container>
    </>
  );
}
