#!/usr/bin/env python3
import os
import sys

# ── Make sure the project root is in the import path ────────────────
# If this file is at /path/to/hackerservice/scripts/create_users.py,
# this adds /path/to/hackerservice to sys.path so `import hackerservice` works.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

# ── Now imports will resolve ────────────────────────────────────────
from hackerservice import create_app, db
from hackerservice.models import User
from hackerservice.models.affiliate import Affiliate
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Ensure at least one Affiliate exists
    aff = Affiliate.query.filter_by(code="AFFILIATE1").first()
    if not aff:
        raise RuntimeError("No Affiliate with code AFFILIATE1 — run create_affiliates.py first")

    # Admin user
    admin = User(
        username="root",
        password_hash=generate_password_hash("changeme"),
        role="admin"
    )
    # Affiliate user (linked to the Affiliate row)
    alice = User(
        username="alice",
        password_hash=generate_password_hash("alicepass"),
        role="affiliate",
        affiliate_id=aff.id
    )

    # Upsert them
    db.session.merge(admin)
    db.session.merge(alice)
    db.session.commit()
    print("✅ Seeded admin and affiliate users:")
    print("   • root / changeme  (admin)")
    print("   • alice / alicepass (affiliate)")

