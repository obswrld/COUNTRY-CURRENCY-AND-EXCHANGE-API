import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my-secret-key')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:LamineYamal10!@localhost:3306/country_exchange_db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False