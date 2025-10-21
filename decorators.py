from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                flash("Acceso no autorizado.", "danger")
                return redirect(url_for('login'))
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