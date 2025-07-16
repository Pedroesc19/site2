# hackerservice/models/affiliate.py
from hackerservice.extensions import db

class Affiliate(db.Model):
    __tablename__ = "affiliates"

    id             = db.Column(db.Integer, primary_key=True)
    code           = db.Column(db.String(32), unique=True, nullable=False)   # e.g. AFF12
    display_name   = db.Column(db.String(80))
    discount_pct   = db.Column(db.Numeric(5, 2), default=0.0)
    commission_pct = db.Column(db.Numeric(5, 2), default=20.0)               # 0–100 %
    is_active      = db.Column(db.Boolean, default=True)

    # optional payout addresses (for future mass-payout helper)
    btc_address = db.Column(db.String(128))
    xmr_address = db.Column(db.String(128))

    # reverse-relation (list of commissions)
    commissions = db.relationship("Commission", back_populates="affiliate")

