#!/usr/bin/env python3
import sys, subprocess, json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Order, Base  # adjust import per your models

# --- Config ---
RPC_USER = "btcapi"
RPC_PASS = open("/run/secretcfg/BTC_RPC_PASS").read().strip()
RPC_CMD = ["bitcoin-cli", f"-rpcuser={RPC_USER}", f"-rpcpassword={RPC_PASS}"]
DB_URL  = "sqlite:////home/darknetadmin/hackerservice/db.sqlite3"  # adjust as needed

def get_txinfo(txid):
    out = subprocess.check_output(RPC_CMD + ["gettransaction", txid])
    return json.loads(out)

def main():
    txid = sys.argv[1]
    info = get_txinfo(txid)
    # Find the receiving address in details[]
    for d in info.get("details", []):
        if d.get("category") == "receive":
            addr   = d["address"]
            amount = d["amount"]  # in BTC
            break
    else:
        return  # no receive record

    # Persist to DB
    engine = create_engine(DB_URL)
    Base.metadata.bind = engine
    Session = sessionmaker(bind=engine)
    session = Session()

    # Assume Order has a btc_address and status field
    order = session.query(Order).filter_by(btc_address=addr).first()
    if not order:
        return

    # Mark paid if >= required amount (in BTC)
    if amount >= order.btc_amount:
        order.status = "paid"
        session.commit()

if __name__ == "__main__":
    main()

