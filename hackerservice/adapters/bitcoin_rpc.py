# hackerservice/adapters/bitcoin_rpc.py

"""
Light wrapper around Bitcoin Core’s JSON-RPC using python-bitcoinrpc,
with automatic wallet loading on demand.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

# Load .env if present
load_dotenv(override=False)

# Parse RPC credentials
login = os.getenv("BTC_RPC_LOGIN") or os.getenv("RPC_LOGIN", "")
if ":" in login:
    RPC_USER, RPC_PASS = login.split(":", 1)
else:
    cfg = Path("/run/secretcfg/bitcoin_rpc.conf")
    if cfg.exists():
        for line in cfg.read_text().splitlines():
            if line.startswith("RPC_LOGIN="):
                _, creds = line.split("=", 1)
                RPC_USER, RPC_PASS = creds.strip().split(":", 1)
                break
    else:
        RPC_USER = RPC_PASS = None

if not RPC_USER or not RPC_PASS:
    raise RuntimeError(
        "Bitcoin RPC credentials not found—set BTC_RPC_LOGIN "
        "or provide /run/secretcfg/bitcoin_rpc.conf"
    )

RPC_PORT    = os.getenv("BTC_RPC_PORT", "8332")
WALLET_NAME = os.getenv("BTC_WALLET_NAME", "sitehot")
_BASE_URI   = f"http://{RPC_USER}:{RPC_PASS}@127.0.0.1:{RPC_PORT}"
_RPC_URI    = f"{_BASE_URI}/wallet/{WALLET_NAME}"


def _load_wallet_if_needed():
    """
    Attempt to load the wallet if it isn't already loaded.
    """
    base_client = AuthServiceProxy(_BASE_URI, timeout=10)
    try:
        base_client.loadwallet(WALLET_NAME)
    except JSONRPCException as e:
        msg = str(e)
        # -4: already loaded, -18: verifying blocks in IBD
        if "already loaded" in msg or "Verifying blocks" in msg:
            return True
        if "Wallet file not found" in msg:
            raise RuntimeError(f"Wallet '{WALLET_NAME}' not found on disk: {e}") from e
        # ignore other loadwallet errors
    return True


def create_btc_address(label: str) -> str:
    """
    Generate a new Bech32 address tagged with the given label.
    If the wallet isn't loaded yet, attempt to load it and retry.
    """
    client = AuthServiceProxy(_RPC_URI, timeout=10)
    try:
        return client.getnewaddress(label, "bech32")  # type: ignore[attr-defined]
    except JSONRPCException as e:
        msg = str(e)
        # -18: wallet not found or not loaded
        if "Requested wallet does not exist" in msg or "-18" in msg:
            _load_wallet_if_needed()
            # retry once
            client = AuthServiceProxy(_RPC_URI, timeout=10)
            try:
                return client.getnewaddress(label, "bech32")  # type: ignore[attr-defined]
            except JSONRPCException as e2:
                raise RuntimeError(f"Bitcoin RPC error after loading wallet: {e2}") from e2
        raise RuntimeError(f"Bitcoin RPC error in getnewaddress: {e}") from e
    finally:
        # ensure the underlying HTTP connection is closed
        try:
            client._AuthServiceProxy__conn.close()
        except Exception:
            pass


def get_transaction(txid: str) -> dict:
    """
    Return the result of the `gettransaction` RPC call as a dict.
    """
    client = AuthServiceProxy(_RPC_URI, timeout=10)
    try:
        return client.gettransaction(txid)  # type: ignore[attr-defined]
    except JSONRPCException as e:
        raise RuntimeError(f"Bitcoin RPC error in gettransaction: {e}") from e
    finally:
        try:
            client._AuthServiceProxy__conn.close()
        except Exception:
            pass

