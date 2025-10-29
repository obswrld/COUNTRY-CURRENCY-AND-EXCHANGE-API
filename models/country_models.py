import random
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Country(db.Model):
    __tablename__ = 'countries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    capital = db.Column(db.String(100), nullable=True)
    region = db.Column(db.String(100), nullable=True)
    population = db.Column(db.BigInteger, nullable=True)
    currency_code = db.Column(db.String(10), nullable=True)
    exchange_rate = db.Column(db.Float, nullable=True)
    estimated_gdp = db.Column(db.Float, nullable=True)
    flag_url = db.Column(db.String(255), nullable=True)
    last_refreshed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def update_gdp(self):
        if self.exchange_rate and self.exchange_rate > 0 and self.population:
            multiplier = random.randint(1000, 2000)
            self.estimated_gdp = (self.population * multiplier) / self.exchange_rate
        else:
            self.estimated_gdp = 0

class RefreshInfo(db.Model):
    __tablename__ = 'refresh_info'
    refresh_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    last_refreshed_at = db.Column(db.DateTime, nullable=True)
    total_countries = db.Column(db.Integer, nullable=True)
