import secrets
from flask import session


def new_captcha() -> str:
    """Generate a simple math question and store the numeric answer."""
    a = secrets.randbelow(10)
    b = secrets.randbelow(10)
    session['captcha'] = a + b
    return f"What is {a} + {b}?"


def validate(response: str) -> bool:
    """Return True iff the user-supplied answer matches the stored one."""
    expected = session.pop('captcha', None)
    if expected is None:
        return False
    try:
        return int(response.strip()) == int(expected)
    except (ValueError, TypeError):
        return False
