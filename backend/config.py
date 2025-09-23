# backend/config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-that-you-should-change'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is not set. Please configure it in your .env file.")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM API Keys
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL')
    MAX_CHAT_HISTORY_LENGTH = int(os.environ.get('MAX_CHAT_HISTORY_LENGTH', 10))

    # Apollo LLM API settings
    APOLLO_CLIENT_ID = os.environ.get('APOLLO_CLIENT_ID')
    APOLLO_CLIENT_SECRET = os.environ.get('APOLLO_CLIENT_SECRET')
    APOLLO_TOKEN_URL = os.environ.get('APOLLO_TOKEN_URL')
    APOLLO_LLM_API_BASE_URL = os.environ.get('APOLLO_LLM_API_BASE_URL')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

def get_config():
    return DevelopmentConfig if os.environ.get('FLASK_ENV') == 'development' else ProductionConfig