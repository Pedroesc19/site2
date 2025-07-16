import secrets
from flask import session


def new_captcha() -> str:
    """Generate a simple math question and store the answer in the session."""
    a = secrets.randbelow(10)
    b = secrets.randbelow(10)
    session['captcha'] = str(a + b)
    return f"What is {a} + {b}?"


def validate(response: str) -> bool:
    """Return True iff the user-supplied answer matches the stored one."""
    return response.strip() == session.pop('captcha', '')
