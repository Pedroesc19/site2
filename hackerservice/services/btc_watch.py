import requests, time, sqlite3
ESPLORA = "https://blockstream.info/api"

def addr_balance(addr):
    return int(requests.get(f"{ESPLORA}/address/{addr}").json()["chain_stats"]["funded_txo_sum"])

def watch():
    db = sqlite3.connect("/home/darknetadmin/hackerservice/db.sqlite3")
    cur = db.cursor()
    while True:
        cur.execute("SELECT id, btc_address, status FROM orders WHERE status='pending'")
        for oid, addr, _ in cur.fetchall():
            if addr and addr_balance(addr) > 0:
                cur.execute("UPDATE orders SET status='paid' WHERE id=?", (oid,))
                db.commit()
                # here also call payout() etc.
                print("Order", oid, "paid")
        time.sleep(30)

