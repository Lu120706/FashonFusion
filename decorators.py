from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_role = session.get("role")

            if user_role != required_role:
                flash("🚫 No tienes permisos para acceder a esta sección.", "danger")
                return redirect(url_for("home.index"))  # Cambia si tu home es otra ruta

            return f(*args, **kwargs)
        return wrapper
    return decorator

def find_or_create_role(db, Rol, nombre):
    """Busca un rol por nombre o lo crea si no existe."""
    role = Rol.query.filter_by(nombre=nombre).first()
    if not role:
        role = Rol(nombre=nombre)
        db.session.add(role)
        db.session.commit()
    return role
