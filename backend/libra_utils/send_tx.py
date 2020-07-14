import sys
from pylibra import LibraNetwork

from libra_utils.custody import Custody
from libra_utils.types.currencies import LibraCurrency
from libra_utils.libra import decode_full_addr, mint_and_wait
from libra_utils.vasp import Vasp


def send_tx(amount, bech32_addr):
    vasp_addr, subaddr = decode_full_addr(bech32_addr)
    version, seq = v.send_transaction(LibraCurrency.LBR, amount, vasp_addr, subaddr)
    print(version, seq)


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print(f"usage: {__file__} <amount_microlibra> <bech32_address>")
        exit()

    custody = Custody()
    custody.init()

    v = Vasp("wallet")
    v.setup_blockchain()
    mint_and_wait(v.vasp_auth_key, 100_000 * 1_000_000, LibraCurrency.LBR)
    send_tx(int(sys.argv[1]), sys.argv[2])

    # print balances
    api = LibraNetwork()
    ac = api.getAccount(v.vasp_address)
    print(f"Balances: {ac.balances}")
