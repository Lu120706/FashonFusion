# app.py
from flask import Flask
from config import Config
from extensions import db, login_manager
from models import Usuario, Rol
from routes import *  # importa todas las rutas desde routes/__init__.py

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
