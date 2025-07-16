#!/usr/bin/env python3
import sys, os
from pathlib import Path

# ensure that `import hackerservice` works
proj_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(proj_root))

from hackerservice import create_app, db
from hackerservice.models.affiliate import Affiliate

app = create_app()
with app.app_context():
    affiliates = [
        Affiliate(code="AFFILIATE1", display_name="Alice", commission_pct=30),
        Affiliate(code="BETA",       display_name="Beta Tester", commission_pct=15),
    ]
    for a in affiliates:
        db.session.merge(a)
    db.session.commit()
    print(f"Seeded {len(affiliates)} affiliates.")
