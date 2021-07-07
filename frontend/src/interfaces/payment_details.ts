export interface PaymentDetails {
  action: string;
  amount: number;
  currency: string;
  expiration: number;
  merchant_name: string;
  reference_id: string;
  vasp_address: string;
  demo: boolean;
}
