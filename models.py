from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin

class Rol(db.Model):
    __tablename__ = 'rol'
    id_rol = db.Column(db.String(1), primary_key=True)
    nombre = db.Column(db.String(25), nullable=False)
    fecha_registro = db.Column(db.DateTime, server_default=db.func.now())

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.String(15), primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(150), unique=True)
    contrasena = db.Column(db.String(255))
    direccion = db.Column(db.String(255))
    id_rol = db.Column(db.String(1), db.ForeignKey('rol.id_rol'))
    creado_en = db.Column(db.DateTime, server_default=db.func.now())
    actualizado_en = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def set_password(self, raw):
        self.contrasena = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.contrasena, raw) if self.contrasena else False

    def get_id(self):
        return str(self.id_usuario)

class Producto(db.Model):
    __tablename__ = 'productos'
    id_producto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)
    talla = db.Column(db.String(20))
    color = db.Column(db.String(25))
    precio_producto = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    disponibilidad = db.Column(db.Enum('SI', 'NO'), nullable=False, default='SI')
    stock = db.Column(db.Integer, nullable=False, default=0)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

class Factura(db.Model):
    __tablename__ = 'factura'
    id_factura = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.String(15), db.ForeignKey('usuarios.id_usuario'), nullable=False)
    direccion_envio = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.Enum('pendiente', 'pagada', 'enviada', 'cancelada'), default='pendiente')
    total = db.Column(db.Numeric(10, 2), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

class FacturaItem(db.Model):
    __tablename__ = 'factura_items'

    id_item = db.Column(db.Integer, primary_key=True)
    id_factura = db.Column(db.Integer, db.ForeignKey('factura.id_factura'), nullable=False)
    id_producto = db.Column(db.Integer, db.ForeignKey('productos.id_producto'), nullable=True)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    nombre_producto = db.Column(db.String(255))
    talla = db.Column(db.String(20))
    color = db.Column(db.String(25))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship('Producto', backref='factura_items', lazy=True)
    factura = db.relationship('Factura', backref=db.backref('items', lazy=True))

    def calcular_subtotal(self):
        """Calcula el subtotal automáticamente."""
        self.subtotal = self.cantidad * self.precio_unitario