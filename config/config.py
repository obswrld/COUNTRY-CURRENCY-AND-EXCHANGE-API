import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DB_URI', 'mysql+pymysql://root:LamineYamal%21@localhost:3306/country_exchange_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False