# routes/productos.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    abort, current_app
)
from werkzeug.utils import secure_filename
import datetime
import os
from extensions import db
from models import Producto
from decorators import role_required  # asumes que este decorador existe y usa session

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")

# -----------------------
# RUTAS ADMIN (CRUD)
# -----------------------

@productos_bp.route('/admin/products')
@role_required('admin')
def admin_products():
    productos = Producto.query.order_by(Producto.creado_en.desc()).all()
    return render_template('admin_products.html', productos=productos)


@productos_bp.route('/admin/products/new', methods=['GET', 'POST'])
@role_required('admin')
def admin_create_product():
    if request.method == 'POST':
        # recoger campos (asegúrate de que tus inputs tengan estos name en el formulario)
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        categoria = request.form.get('categoria', '').strip()
        talla = request.form.get('talla', '').strip()
        color = request.form.get('color', '').strip()
        # asegurar valores por defecto y validaciones mínimas
        try:
            precio = float(request.form.get('precio_producto', 0))
        except ValueError:
            precio = 0.0
        disponibilidad = request.form.get('disponibilidad', 'SI')
        try:
            stock = int(request.form.get('stock', 0))
        except ValueError:
            stock = 0

        # Manejo seguro de la foto: guardamos en la carpeta estática del app
        foto_filename = None
        if 'foto_producto' in request.files:
            f = request.files['foto_producto']
            if f and f.filename:
                filename = secure_filename(f.filename)
                ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
                filename = f"{ts}_{filename}"
                upload_path = os.path.join(current_app.static_folder, 'uploads', 'productos')
                os.makedirs(upload_path, exist_ok=True)
                f.save(os.path.join(upload_path, filename))
                # Guardamos la ruta relativa dentro de static (ej: uploads/productos/xxx.jpg)
                foto_filename = os.path.join('uploads', 'productos', filename)

        nuevo = Producto(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,
            talla=talla,
            color=color,
            precio_producto=precio,
            disponibilidad=disponibilidad,
            stock=stock,
            foto_producto=foto_filename
        )
        db.session.add(nuevo)
        try:
            db.session.commit()
            flash('✅ Producto creado con éxito', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error creando producto")
            flash(f'❌ Error al crear producto: {e}', 'danger')
        return redirect(url_for('productos.admin_products'))

    # GET: formulario
    return render_template('product_form.html', action='Crear', producto=None)


@productos_bp.route('/admin/products/edit/<int:id_producto>', methods=['GET', 'POST'])
@role_required('admin')
def admin_edit_product(id_producto):
    producto = Producto.query.get_or_404(id_producto)

    if request.method == 'POST':
        producto.nombre = request.form.get('nombre', producto.nombre).strip()
        producto.descripcion = request.form.get('descripcion', producto.descripcion).strip()
        producto.categoria = request.form.get('categoria', producto.categoria).strip()
        producto.talla = request.form.get('talla', producto.talla).strip()
        producto.color = request.form.get('color', producto.color).strip()
        try:
            producto.precio_producto = float(request.form.get('precio_producto', producto.precio_producto))
        except Exception:
            pass
        producto.disponibilidad = request.form.get('disponibilidad', producto.disponibilidad)
        try:
            producto.stock = int(request.form.get('stock', producto.stock))
        except Exception:
            pass

        if 'foto_producto' in request.files:
            f = request.files['foto_producto']
            if f and f.filename:
                filename = secure_filename(f.filename)
                ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
                filename = f"{ts}_{filename}"
                upload_path = os.path.join(current_app.static_folder, 'uploads', 'productos')
                os.makedirs(upload_path, exist_ok=True)
                f.save(os.path.join(upload_path, filename))
                producto.foto_producto = os.path.join('uploads', 'productos', filename)

        try:
            db.session.commit()
            flash('✅ Producto actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error actualizando producto")
            flash(f'❌ Error actualizando producto: {e}', 'danger')
        return redirect(url_for('productos.admin_products'))

    return render_template('product_form.html', action='Editar', producto=producto)


@productos_bp.route('/admin/products/delete/<int:id_producto>', methods=['POST'])
@role_required('admin')
def admin_delete_product(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    db.session.delete(producto)
    try:
        db.session.commit()
        flash('✅ Producto eliminado', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error eliminando producto")
        flash(f'❌ Error eliminando: {e}', 'danger')
    return redirect(url_for('productos.admin_products'))

# Catálogo (lista)
@productos_bp.route("/")
def catalogo():
    productos = Producto.query.all()
    return render_template("catalogo.html", productos=productos)

# Detalle de producto (uno solo)
@productos_bp.route("/<int:pid>")
def detalle(pid):
    product = Producto.query.get(pid)
    if not product:
        abort(404)
    return render_template("productos.html", product=product)