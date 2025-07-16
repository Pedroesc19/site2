import os, itertools
from bitcoinlib.keys import HDKey

XPUB = os.getenv("SITEHOT_XPUB")
_hd  = HDKey(import_key=XPUB)

# simple counter persisted to disk
_counter_path = "/home/darknetadmin/hackerservice/hot_counter.txt"
def _next_index():
    try:
        i = int(open(_counter_path).read()) + 1
    except FileNotFoundError:
        i = 0
    open(_counter_path,"w").write(str(i))
    return i

def create_btc_address(label: str) -> str:
    idx = _next_index()
    child = _hd.subkey_for_path(f"0/{idx}")   # BIP-44 receive chain
    return child.address()

