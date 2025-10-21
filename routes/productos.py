# routes/productos.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from werkzeug.utils import secure_filename
import datetime, os
from app import db
from models import Producto
from decorators import role_required # si lo tienes en otro archivo, ajústalo

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/admin/products')
@role_required('admin')
def admin_products():
    productos = Producto.query.order_by(Producto.creado_en.desc()).all()
    return render_template('admin_products.html', productos=productos)


@productos_bp.route('/admin/products/new', methods=['GET', 'POST'])
@role_required('admin')
def admin_create_product():
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        categoria = request.form['categoria']
        talla = request.form['talla']
        color = request.form['color']
        precio = float(request.form['precio_producto'])
        disponibilidad = request.form['disponibilidad']
        stock = int(request.form['stock'])
        foto_filename = None

        if 'foto_producto' in request.files:
            f = request.files['foto_producto']
            if f and f.filename:
                filename = secure_filename(f.filename)
                ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
                filename = f"{ts}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'productos')
                os.makedirs(upload_path, exist_ok=True)
                f.save(os.path.join(upload_path, filename))
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
            flash('❌ Error al crear producto', 'danger')
        return redirect(url_for('productos.admin_products'))

    return render_template('product_form.html', action='Crear', producto=None)


@productos_bp.route('/admin/products/edit/<int:id_producto>', methods=['GET', 'POST'])
@role_required('admin')
def admin_edit_product(id_producto):
    producto = Producto.query.get_or_404(id_producto)
    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.categoria = request.form['categoria']
        producto.talla = request.form['talla']
        producto.color = request.form['color']
        producto.precio_producto = float(request.form['precio_producto'])
        producto.disponibilidad = request.form['disponibilidad']
        producto.stock = int(request.form['stock'])

        if 'foto_producto' in request.files:
            f = request.files['foto_producto']
            if f and f.filename:
                filename = secure_filename(f.filename)
                ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
                filename = f"{ts}_{filename}"
                upload_path = os.path.join('static', 'uploads', 'productos')
                os.makedirs(upload_path, exist_ok=True)
                f.save(os.path.join(upload_path, filename))
                producto.foto_producto = os.path.join('uploads', 'productos', filename)

        try:
            db.session.commit()
            flash('✅ Producto actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {e}', 'danger')
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
        flash(f'❌ Error eliminando: {e}', 'danger')
    return redirect(url_for('productos.admin_products'))


@productos_bp.route('/product/<int:pid>')
def product(pid):
    p = next((x for x in PRODUCTS if x['id'] == pid), None)
    if not p:
        abort(404)
    return render_template('product.html', product=p)