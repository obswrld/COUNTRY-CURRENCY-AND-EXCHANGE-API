from flask import Flask
from config.config import Config
from models.country_models import db
from routes.country_routes import country_db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    app.register_blueprint(country_db)

    return app

if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        db.create_all()
        print("✅ Database tables created (if they did not exist)")

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
