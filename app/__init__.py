# app/__init__.py
from flask import Flask
from flask_pymongo import PyMongo


mongo = PyMongo()


def create_app():
    app = Flask(__name__)

    from app.config import Config
    app.config.from_object(Config)

    mongo.init_app(app)
    app.mongo = mongo

    with app.app_context():
        try:
            mongo.db.command('ping')
            print("MongoDB connected successfully!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")

    from app.places import places as places_blueprint
    app.register_blueprint(places_blueprint)

    return app
