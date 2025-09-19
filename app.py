from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

# -----------------------
# Configuración
# -----------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)

# SQLite por defecto (fácil de probar). Cambia a MySQL si quieres.
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------
# Modelos
# -----------------------
class Rol(db.Model):
    __tablename__ = 'rol'
    id_rol = db.Column(db.String(50), primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    fecha_registro = db.Column(db.DateTime, server_default=db.func.now())

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.String(50), primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(150), unique=True)
    contrasena = db.Column(db.String(255))
    direccion = db.Column(db.String(255))
    id_rol = db.Column(db.String(50), db.ForeignKey('rol.id_rol'))
    creado_en = db.Column(db.DateTime, server_default=db.func.now())
    actualizado_en = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def set_password(self, raw):
        self.contrasena = generate_password_hash(raw)

    def check_password(self, raw):
        if not self.contrasena:
            return False
        return check_password_hash(self.contrasena, raw)

# -----------------------
# Catálogo, carousel y carrito en memoria
# -----------------------
PRODUCTS = [
    {"id": 1, "name": "Camiseta Minimal", "price": 29.99, "desc": "Camiseta de algodón 100%, corte regular.", "image": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800"},
    {"id": 2, "name": "Chaqueta Urbana", "price": 79.50, "desc": "Chaqueta ligera impermeable, ideal para la ciudad.", "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800"},
    {"id": 3, "name": "Pantalón Slim", "price": 49.00, "desc": "Pantalón con stretch, cómodo para todo el día.", "image": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800"},
    {"id": 4, "name": "Sudadera Logo", "price": 59.00, "desc": "Sudadera con capucha y logo bordado.", "image": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=800"},
    {"id": 5, "name": "Gorra Classic", "price": 19.00, "desc": "Gorra ajustable con visera curva.", "image": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800"},
    {"id": 6, "name": "Zapatillas Street", "price": 89.99, "desc": "Zapatillas urbanas para el día a día.", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800"},
    {"id": 7, "name": "Jeans Vintage", "price": 69.99, "desc": "Jeans de corte recto con acabado vintage.", "image": "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=800"},
    {"id": 8, "name": "Bolso Messenger", "price": 45.00, "desc": "Bolso messenger con compartimentos múltiples.", "image": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800"}
]

CAROUSEL_IMAGES = [
    "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=1400",
    "https://images.unsplash.com/photo-1445205170230-053b83016050?w=1400",
    "https://images.unsplash.com/photo-1479064555552-3ef4979f8908?w=1400",
    "https://images.unsplash.com/photo-1463100099107-aa0980c362e6?w=1400"
]

SHOPPING_CARTS = {}

# -----------------------
# Helpers / decoradores
# -----------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Debes iniciar sesión', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(allowed_role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' not in session:
                flash('Debes iniciar sesión', 'warning')
                return redirect(url_for('login'))
            role = session.get('role')
            if role != allowed_role:
                flash('No tienes permisos para acceder a esta página', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# -----------------------
# Context processor (inyecta year globalmente)
# -----------------------
@app.context_processor
def inject_year():
    return {"year": 2025}

# -----------------------
# Rutas principales
# -----------------------
@app.route('/')
def index():
    # Pasamos tanto productos como las imágenes del carrusel
    return render_template('index.html', products=PRODUCTS, carousel_images=CAROUSEL_IMAGES)

# Registro público (rol 'user' por defecto)
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        id_usuario = request.form['id_usuario'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']
        direccion = request.form.get('direccion','').strip()

        if password != confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('register.html')

        if Usuario.query.filter_by(id_usuario=id_usuario).first():
            flash('El id de usuario ya está registrado', 'danger')
            return render_template('register.html')

        if correo and Usuario.query.filter_by(correo=correo).first():
            flash('El correo ya está registrado', 'danger')
            return render_template('register.html')

        # Asegurar que exista el rol 'user'
        rol_user = Rol.query.filter_by(id_rol='user').first()
        if not rol_user:
            rol_user = Rol(id_rol='user', nombre='Usuario')
            db.session.add(rol_user)
            db.session.commit()

        u = Usuario(id_usuario=id_usuario, nombre=nombre, correo=correo, direccion=direccion, id_rol=rol_user.id_rol)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = Usuario.query.filter_by(id_usuario=username).first()
        if user and user.check_password(password):
            session['username'] = user.id_usuario
            session['role'] = user.id_rol  # 'admin' o 'user'
            # inicializar carrito en memoria
            if username not in SHOPPING_CARTS:
                SHOPPING_CARTS[username] = []
            session['cart'] = SHOPPING_CARTS[username]
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    if 'username' in session:
        SHOPPING_CARTS[session['username']] = session.get('cart', [])
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('index'))

# -----------------------
# Productos / carrito
# -----------------------
@app.route('/product/<int:pid>')
def product(pid):
    p = next((x for x in PRODUCTS if x['id'] == pid), None)
    if not p:
        abort(404)
    return render_template('product.html', product=p)

@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', [])
    total = sum(item['price'] for item in cart)
    return render_template('cart.html', cart=cart, total=total)

@app.route('/cart/add/<int:pid>', methods=['POST'])
@login_required
def add_to_cart(pid):
    product = next((p for p in PRODUCTS if p['id'] == pid), None)
    if product:
        session.setdefault('cart', [])
        session['cart'].append(product)
        session.modified = True
        flash(f"{product['name']} agregado al carrito", 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [i for i in session['cart'] if i['id'] != product_id]
        session.modified = True
        flash('Producto eliminado', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/checkout', methods=['POST'])
@login_required
def checkout():
    session['cart'] = []
    session.modified = True
    flash('Compra realizada con éxito', 'success')
    return redirect(url_for('index'))

# -----------------------
# CRUD de usuarios (solo admin)
# -----------------------
@app.route('/admin/users')
@role_required('admin')
def admin_users():
    users = Usuario.query.order_by(Usuario.creado_en.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/new', methods=['GET','POST'])
@role_required('admin')
def admin_create_user():
    if request.method == 'POST':
        id_usuario = request.form['id_usuario'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        password = request.form['password']
        role = request.form.get('role','user').strip()

        if Usuario.query.filter_by(id_usuario=id_usuario).first():
            flash('El id de usuario ya existe', 'danger')
            return render_template('admin_user_form.html', action='Crear', user=None)

        # crear rol si no existe
        r = Rol.query.filter_by(id_rol=role).first()
        if not r:
            r = Rol(id_rol=role, nombre=role.capitalize())
            db.session.add(r)
            db.session.commit()

        u = Usuario(id_usuario=id_usuario, nombre=nombre, correo=correo, id_rol=role)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('Usuario creado', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin_user_form.html', action='Crear', user=None)

@app.route('/admin/users/edit/<string:id_usuario>', methods=['GET','POST'])
@role_required('admin')
def admin_edit_user(id_usuario):
    user = Usuario.query.get_or_404(id_usuario)
    if request.method == 'POST':
        user.nombre = request.form['nombre'].strip()
        user.correo = request.form['correo'].strip()
        new_password = request.form.get('password','').strip()
        user.id_rol = request.form.get('role','user').strip()
        if new_password:
            user.set_password(new_password)
        db.session.commit()
        flash('Usuario actualizado', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin_user_form.html', action='Editar', user=user)

@app.route('/admin/users/delete/<string:id_usuario>', methods=['POST'])
@role_required('admin')
def admin_delete_user(id_usuario):
    # evitar eliminarse a sí mismo
    if id_usuario == session.get('username'):
        flash('No puedes eliminarte a ti mismo', 'warning')
        return redirect(url_for('admin_users'))
    u = Usuario.query.get(id_usuario)
    if u:
        db.session.delete(u)
        db.session.commit()
        flash('Usuario eliminado', 'success')
    else:
        flash('Usuario no encontrado', 'danger')
    return redirect(url_for('admin_users'))

# -----------------------
# Inicializador: crear tablas, roles y admin por defecto
# -----------------------
def create_default_data():
    db.create_all()
    # crear roles si no existen
    if not Rol.query.filter_by(id_rol='admin').first():
        db.session.add(Rol(id_rol='admin', nombre='Administrador'))
    if not Rol.query.filter_by(id_rol='user').first():
        db.session.add(Rol(id_rol='user', nombre='Usuario'))
    db.session.commit()

    # crear admin por defecto si no existe
    if not Usuario.query.filter_by(id_usuario='admin').first():
        admin = Usuario(id_usuario='admin', nombre='Administrador', correo='admin@example.com', id_rol='admin')
        admin.set_password('admin123')  # CAMBIA esta contraseña al desplegar
        db.session.add(admin)
        db.session.commit()

# -----------------------
# Ejecutar app
# -----------------------
if __name__ == '__main__':
    with app.app_context():
        create_default_data()
    app.run(debug=True)