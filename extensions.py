# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

# Extensiones globales
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

# Redirigir al login si el usuario no está autenticado
login_manager.login_view = "usuarios.login"

# Serializador para tokens seguros (reset de contraseña, confirmaciones, etc.)
def get_serializer():
    """Devuelve un serializador para generar tokens seguros."""
    secret_key = current_app.config['SECRET_KEY']
    return URLSafeTimedSerializer(secret_key)
