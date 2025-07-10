# hackerservice/services/captcha.py

import io, secrets, base64
from captcha.image import ImageCaptcha
from flask import session

_IMAGE = ImageCaptcha(width=160, height=60, fonts=None)

def new_captcha() -> str:
    """
    Generate a random 6-char challenge, save it in session['captcha'],
    and return a base-64 PNG <img> data-URI the template can embed.
    """
    challenge = secrets.token_hex(3)[:6].upper()
    session['captcha'] = challenge
    png_bytes = _IMAGE.generate(challenge).getvalue()
    b64 = base64.b64encode(png_bytes).decode()
    return f"data:image/png;base64,{b64}"

def validate(response: str) -> bool:
    """Return True iff the user-supplied text matches the last challenge."""
    return response.strip().upper() == session.pop('captcha', '')
