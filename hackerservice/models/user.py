from hackerservice.extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id             = db.Column(db.Integer, primary_key=True)
    username       = db.Column(db.String(80), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)

    # New fields for auth & affiliate linkage
    role           = db.Column(db.String(16), nullable=False)  # 'admin' or 'affiliate'
    affiliate_id   = db.Column(db.Integer, db.ForeignKey('affiliates.id'))

    # Optional back-ref if you need it
    affiliate      = db.relationship('Affiliate', backref='users', lazy=True)

    def __repr__(self):
        return f"<User {self.username!r} role={self.role!r}>"

