#!/usr/bin/env python3
import subprocess
import psycopg2

# — adjust these to your settings —
DB_URL = "dbname=hackerservice_db user=hackerservice_user password=password host=127.0.0.1"
BTC_CLI = [
    "bitcoin-cli",
    "-datadir=/home/darknetadmin/.bitcoin",
    "-rpcuser=btcapi",
    "-rpcpassword=password",
    "-rpcwallet=sitehot",
]

def get_received(addr):
    out = subprocess.check_output(BTC_CLI + ["getreceivedbyaddress", addr])
    return float(out.strip())

def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, btc_address
        FROM orders
        WHERE status='pending' AND btc_address IS NOT NULL
    """)
    for order_id, addr in cur.fetchall():
        amt = get_received(addr)
        print(f"Order {order_id:<4} → {addr} → received {amt:.8f} BTC")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
