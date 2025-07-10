#!/usr/bin/env python3
import time, os, sys, requests
from requests.auth import HTTPDigestAuth

# Configuration
RPC_URL = "http://127.0.0.1:18090/json_rpc"
RPC_USER = "monero"
RPC_PASS = open("/run/secretcfg/MONERO_PASS").read().strip()
COLD_ADDR = "89LmR862M9nAh23vPBsp2z1yunmLjYdTSiRHmENs4MY3YeQJ5LBC8NXQQoFzSLw4T9hCFk5tAzUAv1XS7UVzDMhF9ZdPN5N"
POLL_INTERVAL = 15  # seconds

auth = HTTPDigestAuth(RPC_USER, RPC_PASS)

def rpc_call(method, params=None):
    payload = {"jsonrpc":"2.0","id":"sweep","method":method, "params": params or {}}
    resp = requests.post(RPC_URL, auth=auth, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data["result"]

def get_unlocked_balance():
    res = rpc_call("get_balance", {"account_index": 0})
    return res["unlocked_balance"] / 1e12  # convert piconero to XMR

def sweep_all():
    print(f"[{time.asctime()}] Sweeping all to cold address {COLD_ADDR}", flush=True)
    res = rpc_call("sweep_all", {"address": COLD_ADDR, "subaddr_indices": []})
    print(f"[{time.asctime()}] Sweep TXs: {res.get('tx_hash_list')}", flush=True)

def main():
    last = 0.0
    while True:
        try:
            bal = get_unlocked_balance()
            if bal > 0:
                sweep_all()
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"[{time.asctime()}] ERROR: {e}", file=sys.stderr, flush=True)
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

