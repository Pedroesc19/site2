# app/utils/monero.py
import os
import requests
from requests.auth import HTTPDigestAuth

# Path to the systemd-provided environment file
RPC_CONF_PATH = "/run/secretcfg/monero_rpc.conf"

# Load RPC credentials from the conf file: expects a line RPC_LOGIN=user:pass
rpc_login = None
if os.path.exists(RPC_CONF_PATH):
    with open(RPC_CONF_PATH) as f:
        for line in f:
            line = line.strip()
            if line.startswith("RPC_LOGIN="):
                rpc_login = line.split("=",1)[1].strip()
                break
if not rpc_login:
    raise RuntimeError(f"RPC_LOGIN not found in {RPC_CONF_PATH}")
RPC_USER, RPC_PASS = rpc_login.split(':', 1)

# Monero wallet RPC endpoint
RPC_URL = "http://127.0.0.1:18090/json_rpc"

# HTTP digest auth for monero-wallet-rpc
auth = HTTPDigestAuth(RPC_USER, RPC_PASS)

def rpc_call(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": method,
        "params": params or {}
    }
    resp = requests.post(RPC_URL, auth=auth, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]

def create_xmr_subaddress(label: str) -> str:
    """
    Generate a unique Monero sub-address for the given label.
    Returns the new XMR address as a string.
    """
    result = rpc_call("create_address", {"account_index": 0, "label": label})
    return result.get("address")

