// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useEffect, useState } from "react";
import { Button, Container } from "reactstrap";
import BackendClient from "../../services/backendClient";
import UsersList from "../../components/UsersList";
import Breadcrumbs from "../../components/Breadcrumbs";
import ErrorMessage from "../../components/Messages/ErrorMessage";
import NewAdminModal, { NewAdminStatus } from "../../components/admin/NewAdmin";
import { User } from "../../interfaces/user";
import { UsernameAlreadyExistsError } from "../../services/errors";
import { useTranslation } from "react-i18next";

export default function Admins() {
  const { t } = useTranslation("admin");
  const [users, setUsers] = useState<User[]>([]);
  const [adminCreationStatus, setAdminCreationStatus] = useState<NewAdminStatus>("inactive");
  const [error, setError] = useState("");

  // Loads the users
  useEffect(() => {
    let isOutdated = false;

    const fetchUsers = async () => {
      try {
        const fetchedUsers = await new BackendClient().getUsers(true);

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

  const createNewAdmin = ({ firstName, lastName, username, password }) => {
    setAdminCreationStatus("sending");

    const asyncCreate = async () => {
      try {
        await new BackendClient().createAdminUser(firstName, lastName, username, password);
        const fetchedUsers = await new BackendClient().getUsers(true);
        setAdminCreationStatus("inactive");
        setUsers(fetchedUsers);
      } catch (e) {
        if (e instanceof UsernameAlreadyExistsError) {
          setError(`User ${username} already exists.`);
        } else {
          setError("Unexpected error.");
        }
        setAdminCreationStatus("failed");
      }
    };

    // noinspection JSIgnoredPromiseFromCall
    asyncCreate();
  };

  const openNewAdmin = () => {
    setAdminCreationStatus("editing");
  };

  const closeNewAdminModal = () => {
    setAdminCreationStatus("inactive");
  };

  const blockUser = async (user_id: number) => {
    try {
      await new BackendClient().blockUser(user_id);
      const fetchedUsers = await new BackendClient().getUsers(true);
      setUsers(fetchedUsers);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <>
      <Breadcrumbs pageName="Administrators" />
      <Container className="py-5">
        <h1 className="h3 text-center">{t("navigation.administrators")}</h1>

        <section className="my-5">
          {users.length === 0 && <ErrorMessage message={t("notifications.no_admins")} />}
          <UsersList users={users} onBlock={blockUser} />
          <div className="my-3 d-flex justify-content-around">
            <Button onClick={openNewAdmin} color="black" outline>
              <i className="fa fa-user-plus" /> {t("newAdmin.button")}
            </Button>
          </div>
        </section>
      </Container>

      <NewAdminModal
        status={adminCreationStatus}
        onClose={closeNewAdminModal}
        onSubmit={createNewAdmin}
        errorMessage={error}
      />
    </>
  );
}
