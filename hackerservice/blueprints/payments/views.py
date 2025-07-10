# app/routes/payments.py

import logging
import json
from flask import Blueprint, request, jsonify
from hackerservice.models import Order  # adjust import based on your ORM
from hackerservice.extensions import db

logger = logging.getLogger(__name__)
bp = Blueprint('payments', __name__, url_prefix='/payments')

# BTC callback (called by bitcoind on new TX)
@bp.route('/btc_callback', methods=['POST'])
def btc_callback():
    data = request.get_json() or {}
    txid = data.get('txid')
    if not txid:
        return jsonify(error='txid missing'), 400

    # TODO: implement your existing record_btc_payment logic here
    try:
        # record_btc_payment(txid)
        logger.info(f'Received BTC callback for {txid}')
        return jsonify(status='ok'), 200
    except Exception as e:
        logger.exception('Error in BTC callback:')
        return jsonify(error=str(e)), 500

# Monero sweeper trigger (optional cron hook)
@bp.route('/xmr_sweep', methods=['POST'])
def xmr_sweep():
    try:
        # import and run auto_sweeper logic
        # from app.scripts.auto_sweeper import main as sweep_main
        # sweep_main()
        logger.info('Triggered XMR sweep')
        return jsonify(status='ok'), 200
    except Exception as e:
        logger.exception('Error triggering XMR sweep:')
        return jsonify(error=str(e)), 500

