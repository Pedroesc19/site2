# hackerservice/services/qr.py

import io, base64
import qrcode

def generate_qr_data_uri(uri: str) -> str:
    """
    Takes any payment URI (e.g. monero:... or bitcoin:...)
    and returns a data-URI PNG QR code.
    """
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"

def generate_monero_qr(address: str, amount_xmr: float) -> str:
    uri = f"monero:{address}?tx_amount={amount_xmr:.12f}"
    return generate_qr_data_uri(uri)
