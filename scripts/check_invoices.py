#!/usr/bin/env python3
import os
import sys

# ─── Ensure the project root is on PYTHONPATH ────────────────────────────────
# If this file lives at /home/darknetadmin/hackerservice/scripts/check_invoices.py,
# this will insert /home/darknetadmin/hackerservice onto sys.path.
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

# ─── Now imports will resolve correctly ─────────────────────────────────────
from hackerservice.adapters.bitcoin_hd import create_btc_address

def main():
    print("Next 5 invoice addresses:")
    for i in range(5):
        label = f"invoice{i}"
        addr  = create_btc_address(label)
        print(f"  [{i:>2}] {label:10s} → {addr}")

if __name__ == "__main__":
    main()

