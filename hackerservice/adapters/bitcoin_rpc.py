# app/utils/bitcoin.py
import os
import subprocess
from pathlib import Path

# Path to the systemd-provided environment file
RPC_CONF_PATH = "/run/secretcfg/bitcoin_rpc.conf"

# Load RPC credentials: look for a line RPC_LOGIN=user:pass
rpc_login = None
if os.getenv("RPC_LOGIN"):
    rpc_login = os.getenv("RPC_LOGIN")
elif Path(RPC_CONF_PATH).exists():
    with open(RPC_CONF_PATH) as f:
        for line in f:
            if line.strip().startswith("RPC_LOGIN="):
                _, val = line.split("=", 1)
                rpc_login = val.strip()
                break

if not rpc_login:
    raise RuntimeError(f"RPC_LOGIN must be set in environment or in {RPC_CONF_PATH}")

# Split into user/pass
try:
    RPC_USER, RPC_PASS = rpc_login.split(":", 1)
except ValueError:
    raise RuntimeError("RPC_LOGIN must be in user:password format")

# Wallet name
WALLET_NAME = "sitehot"

# Base bitcoin-cli command
RPC_CMD = [
    "bitcoin-cli",
    f"-rpcuser={RPC_USER}",
    f"-rpcpassword={RPC_PASS}",
    f"-rpcwallet={WALLET_NAME}",
]

def create_btc_address(label: str) -> str:
    """
    Generate a Bech32 BTC address for the given label.
    """
    try:
        out = subprocess.check_output(
            RPC_CMD + ["getnewaddress", label, "bech32"],
            timeout=10
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Bitcoin RPC error: {e.output.decode().strip()}")
    return out.decode().strip()

