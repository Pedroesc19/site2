#!/usr/bin/env python3
"""
One-shot hot-wallet sweep: send everything (minus fee) to cold storage,
temporarily skipping affiliate payouts.
"""

import os
import sys
import datetime
import requests
from decimal import Decimal as D

# Ensure project root is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hackerservice.app import create_app
from hackerservice.extensions import db
from hackerservice.models import Commission, Order

from bitcoinlib.keys import HDKey
from bitcoinlib.transactions import Transaction

# ── Config ───────────────────────────────────────────────────────────────
ESPLORA   = os.getenv("ESPLORA_API_URL", "https://blockstream.info/api")
XPRV_PATH = "/run/secretcfg/SITEHOT_XPRV"
COLD_ADDR = os.getenv("SITE_COLD_ADDR")       # your cold wallet
FEE_SAT   = int(os.getenv("PAYOUT_FEE_SAT", "1000"))

# Load your xprv
xprv = HDKey(import_key=open(XPRV_PATH).read().strip())

def fetch_utxos(address):
    resp = requests.get(f"{ESPLORA}/address/{address}/utxo")
    resp.raise_for_status()
    utxos = resp.json()
    for u in utxos:
        u["invoice_address"] = address
    return utxos

def broadcast(raw_hex):
    headers = {"Content-Type": "text/plain"}
    resp = requests.post(f"{ESPLORA}/tx", data=raw_hex, headers=headers, timeout=30)
    if not resp.ok:
        err = resp.text.strip()
        raise RuntimeError(f"Broadcast failed ({resp.status_code}): {err}")
    return resp.text.strip()

def main():
    app = create_app()
    with app.app_context():
        # Gather all paid Orders’ UTXOs
        orders = (
            db.session.query(Order)
            .filter_by(status="paid")
            .filter(Order.btc_address.isnot(None))
            .all()
        )
        invoice_map = {
            o.btc_address: o.hd_index
            for o in orders
            if o.hd_index is not None
        }

        all_utxos = []
        for addr, idx in invoice_map.items():
            utxos = fetch_utxos(addr)
            all_utxos.extend(utxos)

        total_in = sum(u["value"] for u in all_utxos)
        print(f"{datetime.datetime.utcnow().isoformat()} Total inputs: {total_in} sat")

        if total_in <= FEE_SAT:
            print("Not enough funds to cover fee; aborting.")
            return

        # Build sweep transaction
        tx = Transaction(network="bitcoin")
        for u in all_utxos:
            idx = invoice_map[u["invoice_address"]]
            key = xprv.subkey_for_path(f"0/{idx}")
            tx.add_input(
                prev_txid=u["txid"],
                output_n=u["vout"],
                value=u["value"],
                keys=key
            )

        change = total_in - FEE_SAT
        tx.add_output(value=change, address=COLD_ADDR)

        tx.sign()
        raw_hex = tx.raw_hex()
        txid = broadcast(raw_hex)

        print(f"{datetime.datetime.utcnow().isoformat()} Swept {change} sat to cold wallet, TX {txid}")

        # Leave Commission rows untouched for now

if __name__ == "__main__":
    main()

