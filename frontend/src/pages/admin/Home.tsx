import React, { useContext } from "react";
import { Button, Container } from "reactstrap";
import WalletLoader from "../../components/WalletLoader";
import { Link } from "react-router-dom";
import BalancesList from "../../components/BalancesList";
import { useTranslation } from "react-i18next";
import { settingsContext } from "../../contexts/app";

function Home() {
  const { t } = useTranslation("admin");
  const [settings] = useContext(settingsContext)!;

  return (
    <Container className="py-5">
      {settings.walletTotals.userCount == -1 ? (
        <WalletLoader />
      ) : (
        <>
          <h1 className="h5 font-weight-normal text-body text-center">
            {settings?.user?.first_name} {settings?.user?.last_name}
          </h1>

          <section className="my-5 text-center">
            <div className="h3 m-0">{settings.walletTotals.userCount}</div>
            {t("registered_users")}
          </section>

          <section className="my-5 text-center">
            <Button tag={Link} to="/admin/liquidity" color="black" outline>
              {t("navigation.liquidity")}
            </Button>
            <Button tag={Link} to="/admin/admins" color="black" outline className="mx-2 mx-sm-4">
              {t("navigation.administrators")}
            </Button>
            <Button tag={Link} to="/admin/users" color="black" outline>
              {t("navigation.users")}
            </Button>
          </section>

          <section className="my-5">
            <h2 className="h5 font-weight-normal text-body">{t("total_balances")}</h2>
            <BalancesList balances={settings.walletTotals.balances} onSelect={() => {}} />
          </section>
        </>
      )}
    </Container>
  );
}
export default Home;
