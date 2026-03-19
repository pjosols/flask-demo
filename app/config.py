# app/config.py
import os


class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/nobel_demo")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JSON_SORT_KEYS = False
    TEMPLATES_AUTO_RELOAD = True
