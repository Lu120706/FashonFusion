# carrito.py
import base64
from decimal import Decimal
from flask import Blueprint, request, session, flash, redirect, url_for, render_template
from flask_login import login_required
from models import Producto

carrito_bp = Blueprint('carrito', __name__)

# -----------------------
# Helpers
# -----------------------
def _get_cart():
    return session.get("cart", {})

def format_currency(value, symbol='$'):
    try:
        v = Decimal(value)
    except Exception:
        return f"{symbol}0.00"
    return f"{symbol}{v:,.2f}"


# -----------------------
# Rutas del carrito
# -----------------------

@carrito_bp.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    producto = Producto.query.get_or_404(product_id)
    talla = request.form.get('talla') or request.form.get('size')
    color = request.form.get('color')

    if not talla or not color:
        flash('Por favor selecciona talla y color antes de añadir al carrito.', 'warning')
        return redirect(url_for('catalog'))

    cart = _get_cart()
    key = f"{product_id}:{talla}:{color}"

    precio_attr = getattr(producto, 'precio_producto', None)
    if precio_attr is None:
        precio_attr = getattr(producto, 'precio', 0)
    try:
        precio_float = float(precio_attr)
    except Exception:
        precio_float = 0.0

    imagen_src = '/static/no-image.png'
    try:
        foto = getattr(producto, 'foto_producto', None)
        if foto:
            imagen_src = 'data:image/jpeg;base64,' + base64.b64encode(foto).decode()
    except Exception:
        imagen_src = '/static/no-image.png'

    if key in cart:
        cart[key]['cantidad'] = int(cart[key].get('cantidad', 0)) + 1
    else:
        cart[key] = {
            'id': product_id,
            'nombre': producto.nombre,
            'precio': precio_float,
            'cantidad': 1,
            'talla': talla,
            'color': color,
            'imagen': imagen_src
        }

    session['cart'] = cart
    session.modified = True

    flash(f"{producto.nombre} agregado al carrito (Talla {talla}, Color {color})", 'success')
    return redirect(url_for('carrito.cart'))


@carrito_bp.route('/carrito')
def view_cart():
    cart = session.get("cart", {})
    carrito = []
    total = 0

    for product_id, item in cart.items():
        subtotal = item["precio"] * item["cantidad"]
        total += subtotal
        carrito.append({
            "id": product_id,
            "nombre": item["nombre"],
            "precio": item["precio"],
            "cantidad": item["cantidad"],
            "talla": item.get("talla", "M"),
            "color": item.get("color", "Negro"),
            "imagen": item.get("imagen", "https://via.placeholder.com/60"),
            "subtotal": subtotal
        })

    return render_template("cart.html", carrito=carrito, total=total)


@carrito_bp.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    key = request.form.get('key')
    action = request.form.get('action')
    cart = _get_cart()

    if not key or key not in cart:
        flash('Elemento no encontrado en el carrito.', 'warning')
        return redirect(url_for('carrito.cart'))

    if action == 'increase':
        cart[key]['cantidad'] += 1
    elif action == 'decrease':
        cart[key]['cantidad'] = max(1, cart[key]['cantidad'] - 1)

    session['cart'] = cart
    session.modified = True
    return redirect(url_for('carrito.cart'))


@carrito_bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get("id")
    talla = request.form.get("talla")
    color = request.form.get("color")

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    if product_id in cart:
        if isinstance(cart[product_id], dict):
            if (cart[product_id].get("talla") == talla and cart[product_id].get("color") == color):
                del cart[product_id]
        elif isinstance(cart[product_id], list):
            cart[product_id] = [
                item for item in cart[product_id]
                if not (item["talla"] == talla and item["color"] == color)
            ]
            if not cart[product_id]:
                del cart[product_id]

    session["cart"] = cart
    flash("Producto eliminado del carrito", "success")
    return redirect(url_for("carrito.view_cart"))


@carrito_bp.route('/cart/clear')
def clear_cart():
    session.pop("cart", None)
    session.modified = True
    flash("Carrito limpiado.", "info")
    return redirect(url_for("carrito.cart"))


@carrito_bp.route('/cart/checkout', methods=['POST'])
@login_required
def cart_checkout():
    session['cart'] = []
    session.modified = True
    flash('Compra realizada con éxito', 'success')
    return redirect(url_for('index'))


@carrito_bp.route('/cart')
@login_required
def cart():
    cart_dict = _get_cart()
    carrito = []
    total = Decimal('0.00')

    for key, item in cart_dict.items():
        precio = Decimal(str(item.get('precio', 0)))
        cantidad = int(item.get('cantidad', 1))
        subtotal = precio * cantidad
        total += subtotal

        carrito.append({
            'key': key,
            'id': item.get('id'),
            'nombre': item.get('nombre'),
            'precio': float(precio),
            'cantidad': cantidad,
            'talla': item.get('talla'),
            'color': item.get('color'),
            'imagen': item.get('imagen'),
            'subtotal': float(subtotal)
        })

    return render_template('cart.html', carrito=carrito, total=float(total))