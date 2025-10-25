# routes/rol.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Rol
from decorators import role_required  # asegúrate que esté en tu proyecto

rol_bp = Blueprint('rol', __name__)

@rol_bp.route("/roles")
@role_required('admin')
def listar_roles():
    roles = Rol.query.order_by(Rol.fecha_registro.desc()).all()
    return render_template("admin_rol.html", roles=roles)

@rol_bp.route("/roles/crear", methods=["POST"])
@role_required('admin')
def crear_rol():
    id_rol = request.form["id_rol"]
    nombre = request.form["nombre"]

    nuevo = Rol(id_rol=id_rol, nombre=nombre)
    db.session.add(nuevo)
    try:
        db.session.commit()
        flash("✅ Rol creado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al crear rol: {e}", "danger")
    return redirect(url_for("rol.listar_roles"))

@rol_bp.route("/roles/editar/<id>", methods=["GET", "POST"])
@role_required('admin')
def editar_rol(id):
    rol = Rol.query.filter_by(id_rol=str(id)).first()
    if not rol:
        flash("⚠️ Rol no encontrado.", "warning")
        return redirect(url_for("rol.listar_roles"))

    if request.method == "POST":
        nombre = request.form.get("nombre")
        if not nombre:
            flash("❌ El nombre no puede estar vacío.", "danger")
            return render_template("roles_edit.html", rol=rol)

        rol.nombre = nombre
        try:
            db.session.commit()
            flash("✅ Rol actualizado correctamente.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error al actualizar: {e}", "danger")
        return redirect(url_for("rol.listar_roles"))

    return render_template("roles_edit.html", rol=rol)

@rol_bp.route("/roles/eliminar/<id>", methods=["POST"])
@role_required('admin')
def eliminar_rol(id):
    rol = Rol.query.filter_by(id_rol=str(id)).first()
    if not rol:
        flash("⚠️ Rol no encontrado.", "warning")
        return redirect(url_for("rol.listar_roles"))

    db.session.delete(rol)
    try:
        db.session.commit()
        flash("✅ Rol eliminado.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al eliminar: {e}", "danger")
    return redirect(url_for("rol.listar_roles"))

@rol_bp.route('/debug/list_roles')
def debug_list_roles():
    try:
        rows = [{"id_rol": r.id_rol, "nombre": r.nombre} for r in Rol.query.all()]
        return {"roles": rows}
    except Exception as e:
        return {"error": str(e)}