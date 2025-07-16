#!/usr/bin/env python3
"""
Retro-populate hd_index for legacy Orders

This one-off script scans your HD wallet indices to match
existing invoice addresses stored in `orders.btc_address`, then
sets `orders.hd_index` so the stateless payout script can sweep them.
"""

import os
import sys
from decimal import Decimal as D

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hackerservice.app       import create_app
from hackerservice.extensions import db
from hackerservice.models    import Order
from bitcoinlib.keys         import HDKey

# ── Configuration ────────────────────────────────────────────────────────
XPRV_PATH = "/run/secretcfg/SITEHOT_XPRV"  # Path to your xprv
MAX_SCAN  = 10000                          # How many indices to scan (adjust if needed)

# ── Bootstrap Flask & DB ────────────────────────────────────────────────
app = create_app()
with app.app_context():
    session = db.session

    # 1) Fetch legacy orders missing hd_index
    legacy_orders = session.query(Order).filter(
        Order.btc_address.isnot(None),
        Order.hd_index.is_(None)
    ).all()
    print(f"Found {len(legacy_orders)} legacy orders to process.")

    # 2) Load master key
    xprv = HDKey(import_key=open(XPRV_PATH).read().strip())

    # 3) Scan addresses until we've mapped all or hit max
    addr_index = {}
    for i in range(MAX_SCAN):
        addr = xprv.subkey_for_path(f"0/{i}").address()
        matches = [o for o in legacy_orders if o.btc_address == addr]
        if matches:
            addr_index[addr] = i
            print(f"Found {len(matches)} order(s) for address {addr} at index {i}")

        # Early exit if we've found all
        if len(addr_index) == len(legacy_orders):
            break

    print(f"Mapped {len(addr_index)}/{len(legacy_orders)} addresses in first {i+1} indices.")

    # 4) Assign indices to orders
    updated = 0
    for order in legacy_orders:
        idx = addr_index.get(order.btc_address)
        if idx is not None:
            order.hd_index = idx
            updated += 1
        else:
            print(f"WARNING: Order {order.id}: address {order.btc_address} not found in first {MAX_SCAN} keys")

    session.commit()
    print(f"Retro-population complete: {updated}/{len(legacy_orders)} orders updated.")

