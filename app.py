# app.py
from flask import Flask
from config import Config
from extensions import db, login_manager, mail
from models import Usuario, Rol
from routes import (
    contraseña_bp,
    factura_bp,
    productos_bp,
    registro_bp,
    rol_bp,
    usuarios_bp,
    carrito_bp
)
from globals import SHOPPING_CARTS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Registrar Blueprints (rutas)
    app.register_blueprint(contraseña_bp)
    app.register_blueprint(factura_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(registro_bp)
    app.register_blueprint(rol_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(carrito_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
