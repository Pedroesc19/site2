#!/usr/bin/env bash
# Called by bitcoind with the TXID as $1
TXID="$1"
# Forward to our Python handler
/usr/bin/env python3 /home/darknetadmin/hackerservice/scripts/record_btc_payment.py "$TXID"

