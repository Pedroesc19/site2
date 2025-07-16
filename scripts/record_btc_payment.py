#!/usr/bin/env python3
"""
bitcoin-cli walletnotify handler:
• Confirms the order
• Calculates affiliate commission
• Sends BTC split (commission + remainder)
• Updates DB rows atomically
"""
import sys, subprocess, json, decimal, datetime
from decimal import Decimal as D
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from hackerservice.models import Order, Affiliate, Commission, Base
from hackerservice.services.pricing import fetch_btc_usd_rate

# --- Config ----------------------------------------------------------------
RPC_USER = "btcapi"
RPC_PASS = open("/run/secretcfg/BTC_RPC_PASS").read().strip()
RPC_CMD  = ["bitcoin-cli", f"-rpcuser={RPC_USER}", f"-rpcpassword={RPC_PASS}"]
COLD_ADDR = "bc1qlw6jhrt5hf0n5kuztr4r77w8cxzqzux2vfvh63"           # admin sweep address
DB_URL  = "sqlite:////home/darknetadmin/hackerservice/db.sqlite3"

# Use Decimal for money math
decimal.getcontext().prec = 10

def cli(*args):
    out = subprocess.check_output(RPC_CMD + list(args))
    return out.decode().strip()

def get_transaction(txid):
    return json.loads(cli("gettransaction", txid))

def main():
    txid = sys.argv[1]
    tx   = get_transaction(txid)

    # Locate receive outputs
    recv_details = [d for d in tx["details"] if d["category"] == "receive"]
    if not recv_details:
        return

    # Extract address+amount
    addr = recv_details[0]["address"]
    amt_btc = D(str(recv_details[0]["amount"]))       # Decimal

    # DB session
    engine = create_engine(DB_URL)
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    db = Session()

    order = db.query(Order).filter_by(btc_address=addr).first()
    if not order:
        return                                # unknown address

    if order.status == "paid":
        return                                # already processed

    # ------------------------------------------------------------
    # 1) Mark order paid
    order.status  = "paid"
    order.paid_ts = datetime.datetime.utcnow()

    # ------------------------------------------------------------
    # 2) Determine commission BTC
    commission_btc = D("0")
    aff = None
    if order.affiliate_id:
        aff = db.query(Affiliate).get(order.affiliate_id)
        if aff and aff.btc_address:
            btc_rate = D(str(fetch_btc_usd_rate()))      # USD/BTC
            commission_btc = (D(str(order.commission_usd)) / btc_rate).quantize(D("0.00000001"))

    # Remainder goes to cold wallet (or stays if you set COLD_ADDR = None)
    remainder_btc = amt_btc - commission_btc - D("0.00001")  # subtract minimal fee pad

    # ------------------------------------------------------------
    # 3) Build outputs map for sendmany
    outputs = {}
    if commission_btc > 0:
        outputs[aff.btc_address] = float(commission_btc)
    if remainder_btc > 0 and COLD_ADDR:
        outputs[COLD_ADDR] = float(remainder_btc)

    # Send split TX
    payout_txid = None
    if outputs:
        payout_txid = cli("sendmany", "", json.dumps(outputs))

    # ------------------------------------------------------------
    # 4) Commission row
    if aff and commission_btc > 0:
        com = Commission(
            order_id     = order.id,
            affiliate_id = aff.id,
            usd_amount   = order.commission_usd,
            status       = "paid",          # immediately paid
            txid         = payout_txid,
            paid_ts      = datetime.datetime.utcnow()
        )
        db.add(com)

    db.commit()

    # Log
    print(f"[{datetime.datetime.utcnow()}] Order {order.id} paid. "
          f"Affiliate {aff.display_name if aff else '-'} got {commission_btc} BTC "
          f"(TX {payout_txid}). Remainder {remainder_btc} BTC to cold.")

if __name__ == "__main__":
    main()

