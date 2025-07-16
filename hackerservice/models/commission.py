# hackerservice/models/commission.py
from hackerservice.extensions import db

class Commission(db.Model):
    __tablename__ = "commissions"

    id           = db.Column(db.Integer, primary_key=True)
    order_id     = db.Column(db.Integer,
                             db.ForeignKey("orders.id", ondelete="CASCADE"),
                             nullable=False)
    affiliate_id = db.Column(db.Integer,
                             db.ForeignKey("affiliates.id"),
                             nullable=False)

    usd_amount   = db.Column(db.Numeric(10, 2), nullable=False)
    status       = db.Column(db.String(20), default="accrued")   # accrued → paid
    txid         = db.Column(db.String(64))
    created_ts   = db.Column(db.DateTime(timezone=True),
                             server_default=db.func.now())
    paid_ts      = db.Column(db.DateTime(timezone=True))

    # reverse links
    order     = db.relationship("Order",     back_populates="commission")
    affiliate = db.relationship("Affiliate", back_populates="commissions")

