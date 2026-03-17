# app/config.py

"""
Configuration settings for the Flask demo application.

This module contains configuration variables used throughout the application,
including database connection settings and security configuration.

Note:
    These values can be overridden by environment variables.
    Default MongoDB database:   book_database
    Default MongoDB collection: books
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class for the application.

    This class defines configuration settings used by Flask and its extensions.
    Values can be overridden using environment variables.
    """

    # MongoDB connection URI - connects to the books demo database
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/vinyl_database")

    # Flask secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")  # Change this in production

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # Additional Flask 3.x options
    JSON_SORT_KEYS = False  # Preserve JSON order in responses
    TEMPLATES_AUTO_RELOAD = True  # Reload templates when they change
