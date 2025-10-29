from flask import Flask
import os
from dotenv import load_dotenv
from models.country_models import db
from routes.country_routes import country_db

def create_app():
    load_dotenv()
    app = Flask(__name__)

    db_uri = os.getenv('DB_URI')
    print("DEBUG → Loaded DB_URI:", db_uri)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(country_db)
    return app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app = create_app()

    with app.app_context():
        from models.country_models import db
        db.create_all()
        print("✅ Database tables created (if they did not exist)")

    app.run(host='0.0.0.0', port=port)

