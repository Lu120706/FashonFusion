import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))

    # Base de datos MySQL
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASS', '')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_NAME = os.environ.get('DB_NAME', 'fashion_fusion')

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email (Gmail)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'fashonfusion140@gmail.com'
    MAIL_PASSWORD = 'szrf rqic mfsl xnxa'
    MAIL_DEFAULT_SENDER = 'fashonfusion140@gmail.com'
