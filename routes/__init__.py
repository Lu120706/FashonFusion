from .carrito import carrito_bp
from .contraseña import contraseña_bp
from .factura import factura_bp
from .productos import productos_bp
from .registro import registro_bp
from .rol import rol_bp
from .usuarios import usuarios_bp
from .home import home_bp   # <- agregado

# Lista de blueprints disponibles (opcional, útil para registro dinámico)
__all__ = [
    'carrito_bp',
    'contraseña_bp',
    'factura_bp',
    'productos_bp',
    'registro_bp',
    'rol_bp',
    'usuarios_bp',
    'home_bp'   # <- agregado
]