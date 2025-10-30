import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "my-secret-key")

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://api_user:LamineYamal10!@shuttle.proxy.rlwy.net:36857/railway"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
