from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_role = session.get("id_rol")  # <-- coincide con login()
            if not user_role or user_role not in roles:
                flash("🚫 No tienes permisos para acceder a esta sección.", "danger")
                return redirect(url_for("usuarios.login"))
            return f(*args, **kwargs)
        return wrapped
    return decorator

def find_or_create_role(db, Rol, nombre):
    """Busca un rol por nombre o lo crea si no existe."""
    role = Rol.query.filter_by(nombre=nombre).first()
    if not role:
        role = Rol(nombre=nombre)
        db.session.add(role)
        db.session.commit()
    return role
