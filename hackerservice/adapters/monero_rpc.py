"""
Monero wallet-RPC helper
"""

import os
import requests
from requests.auth import HTTPDigestAuth

# --------------------------------------------------------------------------- #
# ❶  Credentials come from .env → MONERO_RPC_LOGIN = "user:pass"
# --------------------------------------------------------------------------- #
RPC_LOGIN = os.getenv("MONERO_RPC_LOGIN")
if not RPC_LOGIN:
    raise RuntimeError(
        "Environment variable MONERO_RPC_LOGIN is missing. "
        "Add it to your .env as MONERO_RPC_LOGIN=user:pass"
    )

try:
    RPC_USER, RPC_PASS = RPC_LOGIN.split(":", 1)
except ValueError:  # pragma: no cover
    raise RuntimeError("MONERO_RPC_LOGIN must be in 'user:password' format")

# --------------------------------------------------------------------------- #
# ❷  Endpoint & auth object
# --------------------------------------------------------------------------- #
RPC_URL = os.getenv("MONERO_RPC_URL", "http://127.0.0.1:18090/json_rpc")
auth    = HTTPDigestAuth(RPC_USER, RPC_PASS)

# --------------------------------------------------------------------------- #
# ❸  Thin JSON-RPC wrapper
# --------------------------------------------------------------------------- #
def rpc_call(method: str, params: dict | None = None):
    payload = {
        "jsonrpc": "2.0",
        "id": "0",
        "method": method,
        "params": params or {},
    }
    resp = requests.post(RPC_URL, auth=auth, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):  # pragma: no cover
        raise RuntimeError(data["error"])
    return data["result"]


def create_xmr_subaddress(label: str) -> str:
    """
    Generate a new sub-address under account 0 and return it.
    """
    result = rpc_call("create_address", {"account_index": 0, "label": label})
    return result["address"]

