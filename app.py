import base64
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from sqlalchemy import or_
from flask_login import login_required, current_user
from flask_login import LoginManager, UserMixin, login_user, logout_user
import logging
from datetime import datetime
from decimal import Decimal
from flask_login import LoginManager

# -----------------------
# Configuración
# -----------------------
app = Flask(__name__)

# SECRET_KEY: usa variable de entorno en lugar de hardcodear
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# -----------------------
# Base de datos: MySQL (XAMPP) por defecto
# -----------------------
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'fashion_fusion')

# URI para SQLAlchemy (usando PyMySQL)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
# Si quieres probar con sqlite local, descomenta las siguientes two líneas:
# base_dir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'app.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() in ('1','true','yes')

# -----------------------
# Configuración de correo (usar variables de entorno)
# -----------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'fashonfusion140@gmail.com'
app.config['MAIL_PASSWORD'] = 'szrf rqic mfsl xnxa'
app.config['MAIL_DEFAULT_SENDER'] = 'fashonfusion140@gmail.com'  # usa variable de entorno, NO hardcodear

mail = Mail(app)

# Serializador para tokens seguros
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Logger básico
logging.basicConfig(level=logging.INFO)

db = SQLAlchemy(app)

# -----------------------
# Modelos (sin cambiar estructura)
# -----------------------
class Rol(db.Model):
    __tablename__ = 'rol'
    id_rol = db.Column(db.String(1), primary_key=True)   # se respeta VARCHAR(1) existente
    nombre = db.Column(db.String(25), nullable=False)
    fecha_registro = db.Column(db.DateTime, server_default=db.func.now())

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id_usuario = db.Column(db.String(15), primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(150), unique=True)
    contrasena = db.Column(db.String(255))
    direccion = db.Column(db.String(255))
    id_rol = db.Column(db.String(1), db.ForeignKey('rol.id_rol'))
    creado_en = db.Column(db.DateTime, server_default=db.func.now())
    actualizado_en = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    facturas = db.relationship('Factura', backref='usuario', lazy=True)

    def set_password(self, raw):
        self.contrasena = generate_password_hash(raw)

    def check_password(self, raw):
        if not self.contrasena:
            return False
        return check_password_hash(self.contrasena, raw)
    
class Pqrs(db.Model):
    __tablename__ = 'pqrs'
    id_pqrs = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo = db.Column(db.String(25), nullable=False)
    comentario_pqrs = db.Column(db.Text, nullable=False)
    fecha_hora = db.Column(db.DateTime, default=db.func.current_timestamp())
    foto_pqrs = db.Column(db.String(400), nullable=True)   # ruta/filename
    id_usuario = db.Column(db.String(80), nullable=False)  # guarda session['username']
    estado = db.Column(db.String(30), nullable=False, default='Pendiente')

class Review(db.Model):
    __tablename__ = 'resenas'
    id_resenas = db.Column(db.Integer, primary_key=True, autoincrement=True)  # coincide con tu tabla
    id_producto = db.Column(db.Integer, nullable=False, index=True)
    id_usuario = db.Column(db.String(15), nullable=False, index=True)
    calidad = db.Column(db.SmallInteger, nullable=False)
    comodidad = db.Column(db.SmallInteger, nullable=False)
    comentario_resena = db.Column(db.Text, nullable=False)
    foto_comentario = db.Column(db.LargeBinary, nullable=True)  # longblob en BD
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

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
    foto_producto = db.Column(db.LargeBinary)  # longblob
    stock = db.Column(db.Integer, nullable=False, default=0)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Factura(db.Model):
    __tablename__ = 'factura'
    id_factura = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.String(15), db.ForeignKey('usuarios.id_usuario'), nullable=False)
    direccion_envio = db.Column(db.String(255), nullable=False)
    estado = db.Column(db.Enum('pendiente', 'pagada', 'enviada', 'cancelada'), default='pendiente')
    total = db.Column(db.Numeric(10, 2), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = db.relationship('FacturaItem', backref='factura', cascade='all, delete-orphan')

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
    producto = db.relationship("Producto", backref="factura_items", lazy=True)


# -----------------------
# Catálogo, carousel y carrito en memoria
# -----------------------
PRODUCTS = [
    {"id": 1, "name": "Camiseta ", "price": 50.00, "desc": "Camiseta de corte amplio estilo urbano.", "image": "https://i.pinimg.com/736x/c0/5f/5a/c05f5aa53f9f7e2782cad9213ca212a5.jpg"},
    {"id": 2, "name": "Chaqueta Urbana", "price": 79.00, "desc": "Chaqueta ligera , ideal para la ciudad.", "image": "https://i.pinimg.com/1200x/7a/ea/c2/7aeac28004e959e74f6982c034464b46.jpg"},
    {"id": 3, "name": "Pantalón ", "price": 75.00, "desc": "Pantalón cómodo para todo el día.", "image": "https://i.pinimg.com/736x/27/e1/80/27e1807a18944d6b328d4a1c17a87e74.jpg"},
    {"id": 4, "name": "saco", "price": 59.00, "desc": "saco body con la mejor orma que veras.", "image": "https://i.pinimg.com/1200x/d9/2c/98/d92c98c2b397b63fc786d0160e1e787c.jpg"},
    {"id": 5, "name": "Gorra ", "price": 35.00, "desc": "Gorra ajustable con visera curva.", "image": "https://i.pinimg.com/1200x/13/be/f6/13bef60b33418c0d8f44c12d1c029646.jpg"},
    {"id": 6, "name": "Zapatos dc", "price": 150.00, "desc": "Zapatillas urbanas para el día a día.", "image": "https://i.pinimg.com/1200x/fa/3d/9f/fa3d9f93a07581c936e994a2984c4100.jpg"},
    {"id": 7, "name": "medias", "price": 10.00, "desc": "Medias con diseño moderno y detalles gráficos inspirados en la cultura urbana.", "image": "https://i.pinimg.com/1200x/45/f3/fc/45f3fc74755be341b700966811f9a2ee.jpg"},
    {"id": 8, "name": "conjunto", "price": 250.00, "desc": "conjunto completo para vestir facha .", "image": "https://i.pinimg.com/736x/65/a4/48/65a448da9825759a584742e4bd4ed327.jpg"}
]

CAROUSEL_IMAGES = [
    "https://i.pinimg.com/1200x/25/45/e7/2545e7252e6ae24ba0588acea7b721e3.jpg",
    "https://i.pinimg.com/736x/83/7a/e8/837ae84549733543a095459f9186dcff.jpg",
    "https://i.pinimg.com/1200x/b7/55/79/b755793a03207876cb13ea096ff7e905.jpg",
    "https://i.pinimg.com/1200x/e6/a9/1d/e6a91d80d6fc3d1979b8dbecf41bdc27.jpg"
]

SHOPPING_CARTS = {}

# -----------------------
# Config uploads para reseñas
# -----------------------
ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif'}
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'resenas')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# -----------------------
# Login Manager
# -----------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"   # redirige aquí si no está logueado

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _get_cart():
    """
    Devuelve un diccionario con el carrito garantizado.
    Si la sesión tiene formato antiguo (lista), intenta migrarlo.
    """
    cart = session.get('cart', {})

    # Si venía como lista (formato antiguo), migramos a dict
    if isinstance(cart, list):
        new_cart = {}
        for entry in cart:
            try:
                pid = str(entry.get('id') or entry.get('id_producto') or entry.get('product_id') or '')
                talla = entry.get('talla') or entry.get('size') or ''
                color = entry.get('color') or ''
                if not pid:
                    continue
                key = f"{pid}:{talla}:{color}"
                new_cart[key] = {
                    'id': int(pid),
                    'nombre': entry.get('nombre') or entry.get('name'),
                    'precio': float(entry.get('price') or entry.get('precio') or entry.get('precio_producto') or 0),
                    'cantidad': int(entry.get('cantidad', 1)),
                    'talla': talla,
                    'color': color,
                    'imagen': entry.get('imagen') or entry.get('image') or ''
                }
            except Exception:
                continue
        cart = new_cart
        session['cart'] = cart
        session.modified = True

    # Aseguramos que cart sea dict
    if not isinstance(cart, dict):
        cart = {}
        session['cart'] = cart
        session.modified = True

    return cart


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
    """
    Decorador que acepta 'allowed_role' como:
      - el id corto (ej. 'a' / 'u') almacenado en la tabla rol.id_rol, o
      - el nombre descriptivo (ej. 'admin', 'user').
    Resuelve allowed_role con find_or_create_role() y compara contra session['role'].
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'username' not in session:
                flash('Debes iniciar sesión', 'warning')
                return redirect(url_for('login'))

            # Valor actual de la sesión (puede ser 'a' o 'admin' dependiendo de cómo se guardó)
            current_role = session.get('role')

            # Si coincide textualmente, dejamos pasar (caso simple)
            if current_role == allowed_role:
                return f(*args, **kwargs)

            # Intentamos resolver allowed_role a su id real en la tabla rol
            try:
                resolved = find_or_create_role(allowed_role)
                if resolved and current_role == resolved.id_rol:
                    return f(*args, **kwargs)
            except Exception:
                # Si falla la consulta, intentamos una comprobación por nombre parcial
                try:
                    r = Rol.query.filter(Rol.nombre.ilike(f"%{allowed_role}%")).first()
                    if r and current_role == r.id_rol:
                        return f(*args, **kwargs)
                except Exception:
                    pass

            flash('No tienes permisos para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return decorated
    return decorator

# -----------------------
# Helper: encontrar/crear rol compatible con esquema actual (varchar(1))
# -----------------------
def find_or_create_role(key):
    """
    Busca un rol usando:
      1) id_rol == key
      2) nombre ILIKE %key%
      3) id_rol == first_char_of_key (compatibilidad VARCHAR(1))
    Si no existe, intenta crear usando first_char_of_key como id_rol.
    Retorna el objeto Rol o None si no fue posible.
    """
    if not key:
        return None
    key = str(key).strip()
    # 1) Buscar por id exacto
    r = Rol.query.filter_by(id_rol=key).first()
    if r:
        return r
    # 2) Buscar por nombre
    try:
        r = Rol.query.filter(Rol.nombre.ilike(f"%{key}%")).first()
        if r:
            return r
    except Exception:
        pass

    # 3) Intentar con la primera letra (compatibilidad con varchar(1))
    short_id = key[0].lower()
    r = Rol.query.filter_by(id_rol=short_id).first()
    if r:
        return r

    # 4) Crear uno nuevo usando short_id como id_rol (manejar duplicados)
    new_name = key.capitalize()
    new = Rol(id_rol=short_id, nombre=new_name)
    db.session.add(new)
    try:
        db.session.commit()
        return new
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f"find_or_create_role: no se pudo crear rol '{short_id}': {e}")
        return Rol.query.filter_by(id_rol=short_id).first()

# -----------------------
# Context processor (inyecta year globalmente)
# -----------------------
# -----------------------
# Context processor (inyecta year, is_admin y current_user globalmente)
# -----------------------
@app.context_processor
def inject_globals():
    year = 2025
    role = session.get('role')
    is_admin = False
    if role:
        # acepta tanto el id corto ('a') como el nombre completo ('admin')
        if role in ('a', 'admin'):
            is_admin = True
        else:
            try:
                r = Rol.query.filter(Rol.nombre.ilike('%admin%')).first()
                if r and role == r.id_rol:
                    is_admin = True
            except Exception:
                pass
    return {"year": year, "is_admin": is_admin, "current_user": session.get('username')}


# -----------------------
# Rutas principales
# -----------------------
@app.route('/')
def index():
    return render_template('index.html', products=PRODUCTS, carousel_images=CAROUSEL_IMAGES)

@app.route('/catalog')
def catalog():
    productos = Producto.query.all()
    return render_template('catalog.html', products=productos)

@app.route("/pqrs", methods=["GET", "POST"])
@login_required
def enviar_pqrs():
    # POST = crear PQRS
    if request.method == "POST":
        tipo = request.form.get("tipo", "").strip()
        mensaje = request.form.get("mensaje", "").strip()
        if not tipo or not mensaje:
            flash("Completa tipo y mensaje.", "warning")
            return redirect(url_for("enviar_pqrs"))

        id_usuario = session.get("username")  # según tu modelo
        if not id_usuario:
            flash("Debes iniciar sesión.", "danger")
            return redirect(url_for("login"))

        # manejo de foto
        foto_filename = None
        f = request.files.get("foto")
        if f and f.filename:
            if allowed_file(f.filename):
                filename = secure_filename(f.filename)
                ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                filename = f"{ts}_{filename}"
                dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(dest)
                foto_filename = os.path.join("uploads", "pqrs", filename)  # ruta relativa para static
            else:
                flash("Tipo de archivo no permitido.", "warning")
                return redirect(url_for("enviar_pqrs"))

        nueva = Pqrs(
            tipo=tipo,
            comentario_pqrs=mensaje,
            foto_pqrs=foto_filename,
            id_usuario=str(id_usuario)  # guardamos el username como cadena
        )
        db.session.add(nueva)
        try:
            db.session.commit()
            flash("✅ PQRS enviada con éxito", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.exception("Error guardando PQRS")
            flash("Ocurrió un error al guardar. Intenta de nuevo.", "danger")

        return redirect(url_for("enviar_pqrs"))

    # GET = mostrar formulario + lista del usuario
    id_usuario = session.get("username")
    pqrs_list = []
    if id_usuario:
        pqrs_list = Pqrs.query.filter_by(id_usuario=str(id_usuario)).order_by(Pqrs.fecha_hora.desc()).all()
    return render_template("pqrs.html", pqrs_list=pqrs_list)

@app.route('/admin/pqrs')
@role_required('admin')
def admin_pqrs():
    # Trae TODAS las PQRS sin filtrar por usuario
    todas = Pqrs.query.order_by(Pqrs.fecha_hora.desc()).all()
    app.logger.info("Admin %s cargó admin_pqrs; filas=%d", session.get('username'), len(todas))
    return render_template('admin_pqrs.html', pqrs_list=todas)

@app.route("/admin/pqrs/<int:id_pqrs>/estado", methods=["POST"])
@role_required('admin')   # o la verificación de rol que uses
def admin_change_pqrs_estado(id_pqrs):
    app.logger.info("POST estado: %s user=%s", dict(request.form), session.get('username'))
    nuevo_estado = request.form.get("estado")
    if not nuevo_estado:
        flash("Estado no enviado", "warning")
        return redirect(url_for('admin_pqrs'))

    pq = Pqrs.query.get_or_404(id_pqrs)
    pq.estado = nuevo_estado
    try:
        db.session.commit()
        flash(f"Estado de PQRS #{id_pqrs} actualizado a {nuevo_estado}.", "success")
    except Exception:
        db.session.rollback()
        app.logger.exception("Error actualizando estado PQRS")
        flash("Ocurrió un error al actualizar el estado.", "danger")

    # <-- aquí redirigimos al panel admin (no al listado de usuarios)
    return redirect(url_for('admin_pqrs'))

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

        # Asegurar que exista el rol 'user' (adaptado al esquema actual)
        rol_user = find_or_create_role('user')
        if not rol_user:
            flash('Error creando rol de usuario', 'danger')
            return render_template('register.html')

        # Asegurar direccion no nula (si tu columna no acepta NULL)
        direccion_db = direccion if direccion is not None else ''

        u = Usuario(id_usuario=id_usuario, nombre=nombre, correo=correo, direccion=direccion_db, id_rol=rol_user.id_rol)
        u.set_password(password)
        db.session.add(u)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error al guardar usuario: {e}")
            flash(f'Error al guardar el usuario: {e}', 'danger')
            return render_template('register.html')

        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = Usuario.query.filter_by(id_usuario=username).first()
        if user and user.check_password(password):
            # Guardar sólo lo necesario en session
            session['username'] = user.id_usuario
            session['role'] = user.id_rol  # p.ej. 'a' o 'u'
            app.logger.info(f"Usuario logueado: {user.id_usuario} role: {user.id_rol}")
            # inicializar carrito en memoria si no existe
            if username not in SHOPPING_CARTS:
                SHOPPING_CARTS[username] = []
            session['cart'] = SHOPPING_CARTS[username]
            flash('¡Bienvenido!', 'success')
            return redirect(url_for('admin_users') if user.id_rol == 'a' else url_for('index'))
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
# Recuperación de contraseña
# -----------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = Usuario.query.filter_by(correo=email).first()

        if not user:
            flash('No existe un usuario con ese correo', 'danger')
            return render_template('forgot_password.html')

        # Generar token
        token = s.dumps(email, salt='reset-salt')
        link = url_for('reset_password', token=token, _external=True)

        # Enviar correo
        msg = Message('Recupera tu contraseña',
                      sender=app.config.get('MAIL_USERNAME'),
                      recipients=[email])
        msg.body = f'Usa este enlace para resetear tu contraseña: {link}'
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Error enviando correo: {e}")
            flash(f'Error enviando correo: {e}', 'danger')
            return render_template('forgot_password.html')

        flash('Se envió un enlace a tu correo para recuperar la contraseña.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-salt', max_age=3600)  # válido 1 hora
    except SignatureExpired:
        flash('El enlace expiró, solicita uno nuevo.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm = request.form['confirm_password']

        if new_password != confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('reset_password.html', token=token)

        user = Usuario.query.filter_by(correo=email).first()
        if not user:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('forgot_password'))

        user.set_password(new_password)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando contraseña: {e}', 'danger')
            return render_template('reset_password.html', token=token)

        flash('Tu contraseña fue actualizada. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

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
@login_required  # opcional, según tu app (si quieres que cualquiera vea carrito puedes quitarlo)
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
            'key': key,                   # identificador único dentro del carrito (product:talla:color)
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

@app.route('/cart/clear')
def clear_cart():
    session.pop("cart", None)
    session.modified = True
    flash("Carrito limpiado.", "info")
    return redirect(url_for("cart"))

# -----------------------
# Rutas para reseñas
# -----------------------
# -----------------------
# Rutas para reseñas
# -----------------------

@app.route('/api/guardar_reseña', methods=['POST'])
def guardar_resena():
    id_usuario = session.get('username')
    if not id_usuario:
        return jsonify(success=False, message='Debes iniciar sesión.'), 401

    id_producto = request.form.get('id_producto')
    calidad = request.form.get('calidad')
    comodidad = request.form.get('comodidad')
    comentario = request.form.get('comentario_resena')

    if not id_producto or not calidad or not comodidad:
        return jsonify(success=False, message='Faltan datos.'), 400

    try:
        id_producto = int(id_producto)
        calidad = int(calidad)
        comodidad = int(comodidad)
    except ValueError:
        return jsonify(success=False, message='Valores inválidos.'), 400

    foto_blob = None
    if 'foto_comentario' in request.files:
        f = request.files['foto_comentario']
        if f and f.filename:
            foto_blob = f.read()

    new = Review(
        id_producto=id_producto,
        id_usuario=id_usuario,
        calidad=calidad,
        comodidad=comodidad,
        comentario_resena=comentario,
        foto_comentario=foto_blob
    )
    db.session.add(new)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message='Error interno'), 500

    # IMPORTANT: devolvemos "id_resena" (singular) para que coincida con tu JS
    return jsonify(success=True, resena={
        "id_resena": new.id_resenas,
        "id_usuario": new.id_usuario,
        "calidad": new.calidad,
        "comodidad": new.comodidad,
        "comentario_resena": new.comentario_resena,
        "creado_en": new.creado_en.strftime('%Y-%m-%d %H:%M'),
        "foto_url": url_for('ver_foto_resena', rid=new.id_resenas) if new.foto_comentario else None
    }), 201


@app.route('/api/obtener_reseñas')
def obtener_resenas():
    pid = request.args.get('id_producto', type=int)
    if not pid:
        return jsonify(reseñas=[])
    rows = Review.query.filter_by(id_producto=pid).order_by(Review.creado_en.desc()).all()
    out = []
    for r in rows:
        out.append({
            "id_resena": r.id_resenas,               # <-- nota: id_resena (singular)
            "id_usuario": r.id_usuario,
            "calidad": r.calidad,
            "comodidad": r.comodidad,
            "comentario_resena": r.comentario_resena,
            "creado_en": r.creado_en.strftime('%Y-%m-%d %H:%M'),
            "foto_url": url_for('ver_foto_resena', rid=r.id_resenas) if r.foto_comentario else None
        })
    return jsonify(reseñas=out)


@app.route('/api/foto_resena/<int:rid>')
def ver_foto_resena(rid):
    r = Review.query.get_or_404(rid)
    if not r.foto_comentario:
        return "Sin imagen", 404
    return r.foto_comentario, 200, {"Content-Type": "image/jpeg"}


# ===================== EDITAR RESEÑA =====================
@app.route('/api/editar_reseña', methods=['POST'])
def editar_reseña():
    if "username" not in session:
        return jsonify(success=False, message="Debes iniciar sesión."), 401

    # Tu frontend envía FormData, por eso usamos request.form
    rid = request.form.get("id_resena") or request.form.get("id_resenas")
    if not rid:
        return jsonify(success=False, message="Falta id_resena"), 400
    try:
        rid = int(rid)
    except ValueError:
        return jsonify(success=False, message="id_resena inválido"), 400

    review = Review.query.get_or_404(rid)
    if review.id_usuario != session.get("username"):
        return jsonify(success=False, message="No puedes editar reseñas de otros usuarios."), 403

    # Actualizar campos si vienen
    calidad = request.form.get("calidad")
    comodidad = request.form.get("comodidad")
    comentario = request.form.get("comentario_resena")

    if calidad:
        try:
            review.calidad = int(calidad)
        except ValueError:
            pass
    if comodidad:
        try:
            review.comodidad = int(comodidad)
        except ValueError:
            pass
    if comentario is not None:
        review.comentario_resena = comentario

    # Si viene nueva foto
    if 'foto_comentario' in request.files:
        f = request.files['foto_comentario']
        if f and f.filename:
            review.foto_comentario = f.read()

    db.session.commit()
    return jsonify(success=True, message="Reseña actualizada")


# ===================== ELIMINAR RESEÑA =====================
@app.route('/api/eliminar_reseña', methods=['POST'])
def eliminar_reseña():
    if "username" not in session:
        return jsonify(success=False, message="Debes iniciar sesión."), 401

    data = request.get_json() or {}
    rid = data.get("id_resena") or data.get("id_resenas")
    if not rid:
        return jsonify(success=False, message="Falta id_resena."), 400
    try:
        rid = int(rid)
    except ValueError:
        return jsonify(success=False, message="id_resena inválido."), 400

    review = Review.query.get_or_404(rid)
    if review.id_usuario != session.get("username"):
        return jsonify(success=False, message="No puedes eliminar reseñas de otros usuarios."), 403

    db.session.delete(review)
    db.session.commit()
    return jsonify(success=True, message="Reseña eliminada")

@app.route('/cart/checkout', methods=['POST'])
@login_required
def cart_checkout():
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
        role = request.form.get('role')  # aquí será el id_rol (ej 'a' o 'u')
        direccion_db = request.form.get('direccion','').strip() or ''

        if Usuario.query.filter_by(id_usuario=id_usuario).first():
            flash('El id de usuario ya existe', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)

        # Verificamos que el role exista
        r = Rol.query.filter_by(id_rol=role).first()
        if not r:
            flash('Rol seleccionado no existe', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)

        u = Usuario(id_usuario=id_usuario, nombre=nombre, correo=correo, id_rol=r.id_rol, direccion=direccion_db)
        u.set_password(password)
        db.session.add(u)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creando usuario admin: {e}")
            flash(f'Error creando usuario: {e}', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)

        flash('Usuario creado', 'success')
        return redirect(url_for('admin_users'))

    # GET: pasar lista de roles real
    roles = Rol.query.all()
    return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)


# -----------------------
# Editar usuario (admin)
# -----------------------
@app.route('/admin/users/edit/<string:id_usuario>', methods=['GET','POST'])
@role_required('admin')
def admin_edit_user(id_usuario):
    user = Usuario.query.get_or_404(id_usuario)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        new_password = request.form.get('password','').strip()
        role = request.form.get('role')  # id_rol seleccionado
        direccion_db = request.form.get('direccion','').strip() or ''

        # Validaciones mínimas
        if correo:
            # evitar duplicar correos: si existe otro usuario con ese correo
            other = Usuario.query.filter(Usuario.correo == correo, Usuario.id_usuario != id_usuario).first()
            if other:
                flash('El correo ya está en uso por otro usuario', 'danger')
                roles = Rol.query.all()
                return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)

        user.nombre = nombre
        user.correo = correo
        user.direccion = direccion_db

        # comprobar role
        r = Rol.query.filter_by(id_rol=role).first()
        if not r:
            flash('Rol seleccionado no existe', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)
        user.id_rol = r.id_rol

        if new_password:
            user.set_password(new_password)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error actualizando usuario: {e}")
            flash(f'Error actualizando usuario: {e}', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)

        flash('Usuario actualizado', 'success')
        return redirect(url_for('admin_users'))

    # GET: pasar lista de roles real
    roles = Rol.query.all()
    return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)

@app.route('/admin/users/delete/<string:id_usuario>', methods=['POST'])
@role_required('admin')
def admin_delete_user(id_usuario):
    if id_usuario == session.get('username'):
        flash('No puedes eliminarte a ti mismo', 'warning')
        return redirect(url_for('admin_users'))
    u = Usuario.query.get(id_usuario)
    if u:
        db.session.delete(u)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error eliminando usuario: {e}', 'danger')
            return redirect(url_for('admin_users'))
        flash('Usuario eliminado', 'success')
    else:
        flash('Usuario no encontrado', 'danger')
    return redirect(url_for('admin_users'))

# -----------------------
# Inicializador: crear tablas, roles y admin por defecto
# -----------------------
def create_default_data():
    try:
        db.create_all()
    except Exception as e:
        app.logger.error(f"Error creando tablas: {e}")
        return

    # Crear roles compatibles con el esquema (usar short ids si la tabla espera varchar(1))
    try:
        rol_admin = find_or_create_role('admin')   # intentará usar 'a'
        rol_user = find_or_create_role('user')     # intentará usar 'u'
    except Exception as e:
        app.logger.error(f"Error creando roles por defecto: {e}")
        return

    # Crear admin por defecto, asegurando direccion no nula
    try:
        admin_user = Usuario.query.filter_by(id_usuario='admin').first()
        if not admin_user:
            u = Usuario(
                id_usuario='admin',
                nombre='Administrador',
                correo='admin@fashionfusion.com',
                direccion='N/A',
                id_rol=rol_admin.id_rol
            )
            u.set_password('admin123')  # ⚠️ cámbiala después
            db.session.add(u)
            db.session.commit()
            app.logger.info("Usuario admin creado por defecto (user=admin, pass=admin123)")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creando usuario admin por defecto: {e}")
        
# Ruta útil para debug: confirmar qué base de datos está usando la app
@app.route('/debug/dbinfo')
def debug_dbinfo():
    try:
        engine_url = str(db.engine.url)
    except Exception as e:
        engine_url = f"Error obteniendo engine url: {e}"
    return {"engine": engine_url}

# Rutas temporales de debug (borra/limita después de usarlas)
@app.route('/debug/list_roles')
def debug_list_roles():
    try:
        rows = [{"id_rol": r.id_rol, "nombre": r.nombre} for r in Rol.query.all()]
        return {"roles": rows}
    except Exception as e:
        return {"error": str(e)}
    
@app.route('/debug/session')
def debug_session():
    return {
        "username": session.get('username'),
        "role": session.get('role')
    }

@app.route('/admin/products')
@role_required('admin')
def admin_products():
    productos = Producto.query.order_by(Producto.creado_en.desc()).all()
    return render_template('admin_products.html', productos=productos)


@app.route('/admin/products/new', methods=['GET', 'POST'])
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
                upload_path = os.path.join(app.static_folder, "uploads", "productos")  # mejor en static/uploads/...
                os.makedirs(upload_path, exist_ok=True)
                f.save(os.path.join(upload_path, filename))
                foto_filename = os.path.join("uploads", "productos", filename)  # ruta relativa para servir desde /static/

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
            app.logger.exception("Error creando producto")
            flash('❌ Error al crear producto', 'danger')
        return redirect(url_for('admin_products'))

    return render_template('product_form.html', action='Crear', producto=None)


@app.route('/admin/products/edit/<int:id_producto>', methods=['GET', 'POST'])
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
                upload_path = os.path.join("uploads", "productos")
                os.makedirs(upload_path, exist_ok=True)
                f.save(os.path.join(upload_path, filename))
                producto.foto_producto = filename

        try:
            db.session.commit()
            flash('✅ Producto actualizado', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error: {e}', 'danger')
        return redirect(url_for('admin_products'))

    return render_template('product_form.html', action='Editar', producto=producto)


@app.route('/admin/products/delete/<int:id_producto>', methods=['POST'])
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
    return redirect(url_for('admin_products'))
    
@app.route('/actualizar_estado/<int:id>', methods=['POST'])
def actualizar_estado(id):
    if not session.get('username') or session.get('role') != 'admin':
        flash("No tienes permisos para realizar esta acción", "danger")
        return redirect(url_for('listar_pqrs'))

    nuevo_estado = request.form.get("estado")

    pqrs = Pqrs.query.get_or_404(id)
    pqrs.estado = nuevo_estado
    db.session.commit()

    flash("Estado de la PQRS actualizado correctamente ✅", "success")
    return redirect(url_for('listar_pqrs'))

@app.route("/roles")
@role_required('admin')
def listar_roles():
    roles = Rol.query.order_by(Rol.fecha_registro.desc()).all()
    return render_template("admin_rol.html", roles=roles)


@app.route("/roles/crear", methods=["POST"])
@role_required('admin')
def crear_rol():
    id_rol = request.form["id_rol"]
    nombre = request.form["nombre"]

    nuevo = Rol(id_rol=id_rol, nombre=nombre)
    db.session.add(nuevo)
    db.session.commit()
    flash("Rol creado correctamente.", "success")
    return redirect(url_for("listar_roles"))


@app.route("/roles/editar/<id>", methods=["GET", "POST"])
@role_required('admin')
def editar_rol(id):
    rol = Rol.query.filter_by(id_rol=str(id)).first()
    if not rol:
        flash("Rol no encontrado.", "warning")
        return redirect(url_for("listar_roles"))

    if request.method == "POST":
        nombre = request.form.get("nombre")
        if not nombre:
            flash("El nombre no puede estar vacío.", "danger")
            return render_template("roles_edit.html", rol=rol)

        rol.nombre = nombre
        db.session.commit()
        flash("Rol actualizado correctamente.", "success")
        return redirect(url_for("listar_roles"))

    return render_template("roles_edit.html", rol=rol)


@app.route("/roles/eliminar/<id>", methods=["POST"])
@role_required('admin')
def eliminar_rol(id):
    rol = Rol.query.filter_by(id_rol=str(id)).first()
    if not rol:
        flash("Rol no encontrado.", "warning")
        return redirect(url_for("listar_roles"))

    db.session.delete(rol)
    db.session.commit()
    flash("Rol eliminado.", "success")
    return redirect(url_for("listar_roles"))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = _get_cart()
    if not cart:
        flash("Tu carrito está vacío.", "warning")
        return redirect(url_for('cart'))

    try:
        direccion_envio = request.form.get("direccion_envio", "Sin dirección")
        total = Decimal('0.00')
        items_guardar = []

        # cart: key -> item
        for key, info in cart.items():
            prod_id = int(info.get('id'))
            cantidad = int(info.get('cantidad', 1))
            nombre_producto = info.get('nombre')
            precio_unitario = Decimal(str(info.get('precio', '0')))
            subtotal = precio_unitario * cantidad
            total += subtotal

            items_guardar.append({
                'id_producto': prod_id,
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'subtotal': subtotal,
                'nombre_producto': nombre_producto,
                'talla': info.get('talla'),
                'color': info.get('color')
            })

        factura = Factura(
            id_usuario=str(getattr(current_user, 'id', current_user)),  # ajusta si tu usuario usa otra propiedad
            direccion_envio=direccion_envio,
            total=total,
            estado="pendiente"
        )
        db.session.add(factura)
        db.session.flush()  # para obtener id_factura

        for it in items_guardar:
            item = FacturaItem(
                id_factura=factura.id_factura,
                id_producto=it['id_producto'],
                cantidad=it['cantidad'],
                precio_unitario=it['precio_unitario'],
                subtotal=it['subtotal'],
                nombre_producto=it['nombre_producto'],
                talla=it['talla'],
                color=it['color']
            )
            db.session.add(item)

        db.session.commit()
        session.pop('cart', None)
        flash("Factura creada con éxito. ID: {}".format(factura.id_factura), "success")
        return redirect(url_for("invoice_detail", factura_id=factura.id_factura))

    except Exception as e:
        db.session.rollback()
        flash("Error al crear la factura: {}".format(str(e)), "danger")
        return redirect(url_for('cart'))

@app.route('/invoice/<int:factura_id>')
@login_required
def invoice_detail(factura_id):
    factura = Factura.query.get_or_404(factura_id)
    return render_template("factura.html", factura=factura)

# Ruta: usa product_id para coincidir con el template corregido
@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    producto = Producto.query.get_or_404(product_id)

    talla = request.form.get('talla') or request.form.get('size')
    color = request.form.get('color')

    if not talla or not color:
        flash('Por favor selecciona talla y color antes de añadir al carrito.', 'warning')
        return redirect(url_for('catalog'))  # ajusta si tu vista de catálogo usa otro endpoint

    cart = _get_cart()

    key = f"{product_id}:{talla}:{color}"

    # precio seguro
    precio_attr = getattr(producto, 'precio_producto', None)
    if precio_attr is None:
        precio_attr = getattr(producto, 'precio', 0)
    try:
        precio_float = float(precio_attr)
    except Exception:
        precio_float = 0.0

    # generar imagen para la sesión: si tienes longblob lo convertimos a base64; si no, ruta por defecto
    imagen_src = '/static/no-image.png'
    try:
        foto = getattr(producto, 'foto_producto', None)
        if foto:
            imagen_src = 'data:image/jpeg;base64,' + base64.b64encode(foto).decode()
    except Exception:
        imagen_src = '/static/no-image.png'

    # añadir o aumentar
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
    return redirect(url_for('cart'))  # endpoint que muestra el carrito (ver abajo)

@app.route("/carrito")
def view_cart():
    cart = session.get("cart", {})

    # Convertir a lista de dicts para que la plantilla pueda iterar fácilmente
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

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    key = request.form.get('key')
    action = request.form.get('action')  # 'increase' | 'decrease'
    cart = _get_cart()

    if not key or key not in cart:
        flash('Elemento no encontrado en el carrito.', 'warning')
        return redirect(url_for('cart'))

    if action == 'increase':
        cart[key]['cantidad'] = int(cart[key].get('cantidad', 0)) + 1
    elif action == 'decrease':
        cart[key]['cantidad'] = max(1, int(cart[key].get('cantidad', 1)) - 1)

    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    product_id = request.form.get("id")
    talla = request.form.get("talla")
    color = request.form.get("color")

    if "cart" not in session:
        session["cart"] = {}

    cart = session["cart"]

    if product_id in cart:
        # Si no hay variaciones de talla/color, simplemente eliminar
        if isinstance(cart[product_id], dict):
            if (cart[product_id].get("talla") == talla and
                cart[product_id].get("color") == color):
                del cart[product_id]
        elif isinstance(cart[product_id], list):
            # Buscar en la lista la variante
            cart[product_id] = [
                item for item in cart[product_id]
                if not (item["talla"] == talla and item["color"] == color)
            ]
            if not cart[product_id]:  # Si ya no quedan variantes
                del cart[product_id]

    session["cart"] = cart
    flash("Producto eliminado del carrito", "success")
    return redirect(url_for("view_cart"))

# -----------------------
# Ejecutar app
# -----------------------
if __name__ == '__main__':
    with app.app_context():
        create_default_data()
    app.run(debug=True)
