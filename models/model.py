import random
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Country(db.Model):
    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    capital = db.Column(db.String(100))
    region = db.Column(db.String(100))
    population = db.Column(db.BigInteger, nullable=False)
    currency_code = db.Column(db.String(10))
    exchange_rate = db.Column(db.Float)
    estimated_gdb = db.Column(db.Float)
    flag_url = db.Column(db.String(255))
    last_refreshed_at = db.Column(db.DateTime, dafault=datetime.utcnow)

    def updated_gdb(self):
        if self.exchange_rate and self.exchange_rate > 0:
            multiplier = random.randint(1000, 2000)
            self.estimated_gdb = (self.population * multiplier) / self.exchange_rate
        else:
            self.estimated_gdb = 0