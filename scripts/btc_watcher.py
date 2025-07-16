#!/usr/bin/env python3
"""
BTC Deposit Watcher

Poll a public Esplora API every 30s for pending BTC orders;
when a deposit is detected, mark the Order paid and create the Commission.
"""

import os
import sys
import time
import requests
from decimal import Decimal as D

# ── Ensure project root is on PYTHONPATH so `import hackerservice` works ──
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from hackerservice.app import create_app
from hackerservice.extensions import db
from hackerservice.models import Order, Commission

# ── Configuration ────────────────────────────────────────────────────────
ESPLORA_URL   = os.getenv("ESPLORA_API_URL", "https://blockstream.info/api")
POLL_INTERVAL = int(os.getenv("BTC_WATCH_INTERVAL", 30))

def get_address_funded(addr: str) -> int:
    """
    Return confirmed total satoshis received at addr,
    via the Esplora /address/<addr> chain_stats.funded_txo_sum.
    """
    resp = requests.get(f"{ESPLORA_URL}/address/{addr}")
    resp.raise_for_status()
    stats = resp.json().get("chain_stats", {})
    return int(stats.get("funded_txo_sum", 0))

def process_pending_orders(app):
    with app.app_context():
        pending = (
            db.session.query(Order)
            .filter_by(status="pending")
            .filter(Order.btc_address.isnot(None))
            .all()
        )
        for order in pending:
            try:
                funded = get_address_funded(order.btc_address)
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error fetching {order.btc_address}: {e}")
                continue

            # stored x amount is in BTC, convert to satoshi
            expected_sats = int(D(order.btc_amount) * D("1e8"))
            if funded >= expected_sats:
                # mark order as paid
                order.status = "paid"
                order.paid_ts = db.func.now()

                # create a Commission row (accrued)
                if order.affiliate_id:
                    com = Commission(
                        order_id=order.id,
                        affiliate_id=order.affiliate_id,
                        usd_amount=order.commission_usd,
                        status="accrued",
                    )
                    db.session.add(com)

                db.session.commit()
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Order {order.id} marked paid (addr {order.btc_address}).")

def main():
    app = create_app()

    print(f"Starting BTC watcher (poll every {POLL_INTERVAL}s) …")
    while True:
        try:
            process_pending_orders(app)
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Watcher error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

