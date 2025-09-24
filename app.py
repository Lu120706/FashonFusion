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
import datetime


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
    direccion = db.Column(db.String(255))  # en la BD actual puede ser NOT NULL; al crear usaremos '' si es necesario
    id_rol = db.Column(db.String(1), db.ForeignKey('rol.id_rol'))  # FK a varchar(1)
    creado_en = db.Column(db.DateTime, server_default=db.func.now())
    actualizado_en = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

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
    id_usuario = db.Column(db.String(15), nullable=False)  # viene de session['username']

class Review(db.Model):
    __tablename__ = 'resenas'   # Evita tildes en el nombre de tabla por compatibilidad
    id_resena = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_producto = db.Column(db.Integer, nullable=False, index=True)
    id_usuario = db.Column(db.String(150), nullable=False, index=True)
    calidad = db.Column(db.SmallInteger, nullable=False)    # 1..5
    comodidad = db.Column(db.SmallInteger, nullable=False)  # 1..5
    comentario_resena = db.Column(db.Text, nullable=True)
    foto_path = db.Column(db.String(400), nullable=True)    # nombre de archivo en uploads/resenas
    creado_en = db.Column(db.DateTime, server_default=db.func.now())

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    # Catálogo sin precios ni botones de compra
    return render_template('catalog.html', products=PRODUCTS)

@app.route("/pqrs", methods=["GET", "POST"])
@login_required   # tu decorador custom que verifica session['username']
def enviar_pqrs():
    # Si llegas por GET, sólo muestra la página
    if request.method == "POST":
        # Validaciones básicas
        tipo = request.form.get("tipo", "").strip()
        mensaje = request.form.get("mensaje", "").strip()

        if not tipo or not mensaje:
            flash("Completa tipo y mensaje.", "warning")
            return redirect(url_for("enviar_pqrs"))

        # usuario desde session (consistente con tu login)
        id_usuario = session.get("username")
        if not id_usuario:
            flash("Debes iniciar sesión para enviar PQRS.", "danger")
            return redirect(url_for("login"))

        # Manejo de archivo: guardarlo en disco y almacenar filename
        foto_filename = None
        f = request.files.get("foto")
        if f and f.filename:
            if allowed_file(f.filename):
                filename = secure_filename(f.filename)
                ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                filename = f"{ts}_{filename}"
                dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(dest)
                foto_filename = filename
            else:
                flash("Tipo de archivo no permitido.", "warning")
                return redirect(url_for("enviar_pqrs"))

        nueva = Pqrs(
            tipo=tipo,
            comentario_pqrs=mensaje,
            foto_pqrs=foto_filename,   # si usas LargeBinary, usa f.read() en su lugar
            id_usuario=id_usuario
        )
        db.session.add(nueva)
        try:
            db.session.commit()
            flash("✅ PQRS enviada con éxito", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error guardando PQRS: {e}")
            flash("Ocurrió un error al guardar. Intenta de nuevo.", "danger")

        return redirect(url_for("enviar_pqrs"))

    return render_template("pqrs.html")

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
        size = request.form.get("size")
        color = request.form.get("color")
        item = {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "image": product["image"],
            "size": size,
            "color": color
        }
        session.setdefault('cart', [])
        session['cart'].append(item)
        session.modified = True
        flash(f"{product['name']} agregado al carrito (Talla {size}, Color {color})", 'success')
    return redirect(url_for('cart'))

# -----------------------
# Rutas para reseñas
# -----------------------
@app.route('/api/guardar_reseña', methods=['POST'])
def guardar_resena():
    # Usar sesión para identificar al usuario (más seguro)
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

    foto_path = None
    if 'foto_comentario' in request.files:
        f = request.files['foto_comentario']
        if f and f.filename and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            ts = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            filename = f"{ts}_{filename}"
            dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            f.save(dest)
            foto_path = filename

    new = Review(
        id_producto=id_producto,
        id_usuario=str(id_usuario),
        calidad=calidad,
        comodidad=comodidad,
        comentario_resena=comentario,
        foto_path=foto_path
    )
    db.session.add(new)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error al guardar reseña: {e}")
        return jsonify(success=False, message='Error interno'), 500

    return jsonify(success=True, resena={
        "id_resena": new.id_resena,
        "id_usuario": new.id_usuario,
        "calidad": new.calidad,
        "comodidad": new.comodidad,
        "comentario_resena": new.comentario_resena,
        "creado_en": new.creado_en.strftime('%Y-%m-%d %H:%M'),
        "foto_url": url_for('ver_foto_resena', filename=new.foto_path) if new.foto_path else None
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
            "id_resena": r.id_resena,
            "id_usuario": r.id_usuario,
            "calidad": r.calidad,
            "comodidad": r.comodidad,
            "comentario_resena": r.comentario_resena,
            "creado_en": r.creado_en.strftime('%Y-%m-%d %H:%M'),
            "foto_url": url_for('ver_foto_resena', filename=r.foto_path) if r.foto_path else None
        })
    return jsonify(reseñas=out)

@app.route('/uploads/resenas/<path:filename>')
def ver_foto_resena(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
    
# -----------------------
# Ejecutar app
# -----------------------
if __name__ == '__main__':
    # Antes de correr, asegúrate:
    # 1) Crear la base de datos 'fashion_fusion' en phpMyAdmin
    # 2) Instalar PyMySQL: pip install PyMySQL
    # 3) Poner variables de entorno DB_USER/DB_PASS si usas credenciales diferentes
    with app.app_context():
        create_default_data()
    app.run(debug=True)
