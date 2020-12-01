// Copyright (c) The Diem Core Contributors
// SPDX-License-Identifier: Apache-2.0

import React, { useContext } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import LogoImage from "../assets/img/logo.svg";
import SettingsImage from "../assets/img/gears.svg";
import { settingsContext } from "../contexts/app";

const Header = () => {
  const { t } = useTranslation("layout");
  const [settings] = useContext(settingsContext)!;

  return (
    <>
      <header className="fixed-top d-inline-flex justify-content-between align-items-center">
        <div className="small">
          Running on <strong className="text-capitalize">{settings.network}</strong>
        </div>
        <div className="logo">
          <Link to="/">
            <img src={LogoImage} alt={t("name")} />
          </Link>
        </div>
        {settings.user && (
          <Link to="/settings">
            <img src={SettingsImage} alt={t("actions.settings")} />
          </Link>
        )}
      </header>
      <div className="header-push" />
    </>
  );
};

export default Header;
