# hackerservice/models/order.py
from hackerservice.extensions import db

class Order(db.Model):
    __tablename__ = "orders"

    id            = db.Column(db.Integer, primary_key=True)

    # service & pricing
    slug          = db.Column(db.String(64),  nullable=False)          # service slug
    usd_amount    = db.Column(db.Numeric(10, 2), nullable=False)
    btc_amount    = db.Column(db.Numeric(16, 8))
    xmr_amount    = db.Column(db.Numeric(20, 12))
    discount_usd   = db.Column(db.Numeric(12,2), default=0)    
    

    # crypto deposit addresses (nullable until generated)
    btc_address   = db.Column(db.String(128), unique=True)
    xmr_address   = db.Column(db.String(128), unique=True)

    hd_index    = db.Column(db.Integer, nullable=True)
    # affiliate / discount
    affiliate_id  = db.Column(db.Integer, db.ForeignKey("affiliates.id"))
    discount_code = db.Column(db.String(32))
    commission_usd= db.Column(db.Numeric(10, 2))

    # state
    status        = db.Column(db.String(20), default="pending")  # pending/paid/expired
    created_ts    = db.Column(db.DateTime(timezone=True),
                              server_default=db.func.now())
    paid_ts       = db.Column(db.DateTime(timezone=True))

    # reverse relation
    commission    = db.relationship("Commission",
                                    uselist=False,
                                    back_populates="order",
                                    cascade="all, delete-orphan")

