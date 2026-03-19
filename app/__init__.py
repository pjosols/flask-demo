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

            from app.tools.db_init import create_indexes
            create_indexes()
        except Exception as e:
            print(f"MongoDB connection error: {e}")

    from app.laureates import laureates as laureates_blueprint
    app.register_blueprint(laureates_blueprint)

    return app
