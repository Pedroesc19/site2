#!/usr/bin/env python3
"""
HD-based sweep with optional affiliate payouts disabled.
Collect every 'paid' order’s invoice UTXO and push the entire balance
(minus flat FEE_SAT) into SITE_COLD_ADDR in a single SegWit TX.
"""

import os
import sys
import datetime
import subprocess
import requests
from decimal import Decimal as D

# ── Make project importable ─────────────────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hackerservice.app         import create_app
from hackerservice.extensions  import db
from hackerservice.models      import Order

from bitcoinlib.keys           import HDKey
from bitcoinlib.transactions   import Transaction

# ── Config from env / .env ──────────────────────────────────────────────
ESPLORA    = os.getenv("ESPLORA_API_URL", "https://blockstream.info/api")
XPRV_PATH  = "/run/secretcfg/SITEHOT_XPRV"
COLD_ADDR  = os.getenv("SITE_COLD_ADDR")            # bech32 cold wallet
FEE_SAT    = int(os.getenv("PAYOUT_FEE_SAT", "2000"))

# Load master xprv
xprv = HDKey(import_key=open(XPRV_PATH).read().strip())

# ── Helpers ─────────────────────────────────────────────────────────────
def fetch_utxos(addr: str):
    r = requests.get(f"{ESPLORA}/address/{addr}/utxo", timeout=15)
    r.raise_for_status()
    utxos = r.json() 
    for u in utxos:
        u["invoice_address"] = addr
    return utxos

def broadcast(raw_hex: str) -> str:
    r = requests.post(
        f"{ESPLORA}/tx",
        data=raw_hex,
        headers={"Content-Type": "text/plain"},
        timeout=30,
    )
    if not r.ok:
        raise RuntimeError(
            f"Broadcast failed ({r.status_code}): {r.text.strip()}"
        )
    return r.text.strip()

# ── Main ────────────────────────────────────────────────────────────────
def main():
    app = create_app()
    with app.app_context():
        orders = (
            db.session.query(Order)
            .filter_by(status="paid")
            .filter(Order.hd_index.isnot(None))
            .filter(Order.btc_address.isnot(None))
            .all()
        )

        if not orders:
            print("No paid orders found — nothing to sweep.")
            return

        invoice_map = {o.btc_address: o.hd_index for o in orders}

        # Gather UTXOs
        utxos = []
        for addr in invoice_map.keys():
            utxos.extend(fetch_utxos(addr))

        total_in = sum(u["value"] for u in utxos)
        print(f"{datetime.datetime.utcnow().isoformat()} Total inputs: {total_in} sat")

        if total_in <= FEE_SAT:
            print("Not enough to cover miner fee; aborting.")
            return

        # Build SegWit TX
        tx = Transaction(network="bitcoin")
        tx.segwit = True

        for u in utxos:
            idx       = invoice_map[u["invoice_address"]]
            child_key = xprv.subkey_for_path(f"0/{idx}")

            tx.add_input(
                prev_txid = u["txid"],
                output_n  = u["vout"],
                value     = u["value"],
                keys      = [child_key],               # list!
                address   = u["invoice_address"],      # lets lib infer p2wpkh
            )
            print(
                f"DEBUG after adding {u['txid']}:{u['vout']} → inputs now: {len(tx.inputs)}"
            )

        # Single output to cold wallet
        change = total_in - FEE_SAT
        tx.add_output(value=change, address=COLD_ADDR)

        # Debug: fee-rate
        estimated_vsize = tx.vsize
        fee_rate        = FEE_SAT / estimated_vsize
        print(
            f"DEBUG: inputs={len(tx.inputs)}, vsize≈{estimated_vsize}, "
            f"fee={FEE_SAT} sat, rate≈{fee_rate:.2f} sat/vB"
        )

        tx.sign()
        raw_hex = tx.raw_hex()
        print("DEBUG raw length:", len(raw_hex))

        # Optional local decode for sanity
        try:
            subprocess.check_output(
                ["bitcoin-cli", "decoderawtransaction", raw_hex],
                stderr=subprocess.STDOUT,
            )
            print("decoderawtransaction OK")
        except Exception as e:
            print("WARNING: decoderawtransaction failed, but attempting broadcast…")

        txid = broadcast(raw_hex)
        print(
            f"{datetime.datetime.utcnow().isoformat()} Swept {change} sat "
            f"to cold wallet, TX {txid}"
        )

if __name__ == "__main__":
    main()

