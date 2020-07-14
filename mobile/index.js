import { Navigation } from "react-native-navigation";
import Home from "./src/screens/Home";
import Wallet from "./src/screens/Wallet";
import Transactions from "./src/screens/Transactions";
import SingleTransaction from "./src/screens/SingleTransaction";
import Verify from "./src/screens/Verify";
import Settings from "./src/screens/Settings";
import AddCreditCard from "./src/screens/AddCreditCard";
import AddBankAccount from "./src/screens/AddBankAccount";
import Transfer from "./src/screens/Transfer";
import Deposit from "./src/screens/Transfer/Deposit";
import DepositReview from "./src/screens/Transfer/DepositReview";
import Withdraw from "./src/screens/Transfer/Withdraw";
import WithdrawReview from "./src/screens/Transfer/WithdrawReview";
import Convert from "./src/screens/Transfer/Convert";
import ConvertReview from "./src/screens/Transfer/ConvertReview";
import Send from "./src/screens/Send/Send";
import SendScanQR from "./src/screens/Send/SendScanQR";
import SendReview from "./src/screens/Send/SendReview";
import Receive from "./src/screens/Receive";
import SignIn from "./src/screens/SignIn";
import SignUp from "./src/screens/SignUp";
import ForgotPassword from "./src/screens/ForgotPassword";
import ResetPassword from "./src/screens/ResetPassword";
import SessionStorage from "./src/services/sessionStorage";
import "./src/i18n";

console.disableYellowBox = true;

Navigation.registerComponent("Home", () => Home);
Navigation.registerComponent("Wallet", () => Wallet);
Navigation.registerComponent("Transactions", () => Transactions);
Navigation.registerComponent("SingleTransaction", () => SingleTransaction);
Navigation.registerComponent("Verify", () => Verify);
Navigation.registerComponent("Settings", () => Settings);
Navigation.registerComponent("AddCreditCard", () => AddCreditCard);
Navigation.registerComponent("AddBankAccount", () => AddBankAccount);
Navigation.registerComponent("Transfer", () => Transfer);
Navigation.registerComponent("Deposit", () => Deposit);
Navigation.registerComponent("DepositReview", () => DepositReview);
Navigation.registerComponent("Withdraw", () => Withdraw);
Navigation.registerComponent("WithdrawReview", () => WithdrawReview);
Navigation.registerComponent("Convert", () => Convert);
Navigation.registerComponent("ConvertReview", () => ConvertReview);
Navigation.registerComponent("Send", () => Send);
Navigation.registerComponent("SendScanQR", () => SendScanQR);
Navigation.registerComponent("SendReview", () => SendReview);
Navigation.registerComponent("Receive", () => Receive);

Navigation.registerComponent("SignIn", () => SignIn);
Navigation.registerComponent("SignUp", () => SignUp);
Navigation.registerComponent("ForgotPassword", () => ForgotPassword);
Navigation.registerComponent("ResetPassword", () => ResetPassword);

Navigation.events().registerAppLaunchedListener(async () => {
  Navigation.setDefaultOptions({
    topBar: {
      visible: false,
    },
  });
  Navigation.setRoot({
    root: {
      stack: {
        id: "Home",
        children: [
          {
            component: {
              name: (await SessionStorage.getAccessToken()) ? "Home" : "SignIn",
            },
          },
        ],
      },
    },
  });
});
