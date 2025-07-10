from hackerservice.extensions import db

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    # TODO: flesh out schema: slug, amounts, addresses, status, timestamps, etc.
