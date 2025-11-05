from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user
from models import Usuario, Rol, db
from decorators import role_required, find_or_create_role
from globals import SHOPPING_CARTS

usuarios_bp = Blueprint('usuarios', __name__)

# -----------------------
# LOGIN / LOGOUT
# -----------------------
@usuarios_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = Usuario.query.filter_by(id_usuario=username).first()

        if user and user.check_password(password):
            login_user(user)
            session.permanent = True
            session['username'] = user.id_usuario
            session['role'] = user.id_rol

            if username not in SHOPPING_CARTS:
                SHOPPING_CARTS[username] = []
            session['cart'] = SHOPPING_CARTS[username]

            flash('¡Bienvenido!', 'success')
            return redirect(url_for('usuarios.admin_users') if user.id_rol == 'a' else url_for('index'))

        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')


@usuarios_bp.route('/logout')
def logout():
    if 'username' in session:
        SHOPPING_CARTS[session['username']] = session.get('cart', [])
    session.clear()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('index'))


# -----------------------
# CRUD DE USUARIOS (solo admin)
# -----------------------
@usuarios_bp.route('/admin/users')
@role_required('a', 'admin')  # ✅ cambio mínimo aquí
def admin_users():
    users = Usuario.query.order_by(Usuario.creado_en.desc()).all()
    return render_template('admin_users.html', users=users)


@usuarios_bp.route('/admin/users/new', methods=['GET', 'POST'])
@role_required('a', 'admin')  # ✅ cambio mínimo aquí
def admin_create_user():
    if request.method == 'POST':
        id_usuario = request.form['id_usuario'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        password = request.form['password']
        role = request.form.get('role')
        direccion_db = request.form.get('direccion', '').strip() or ''

        if Usuario.query.filter_by(id_usuario=id_usuario).first():
            flash('El id de usuario ya existe', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)

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
            flash(f'Error creando usuario: {e}', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)

        flash('Usuario creado', 'success')
        return redirect(url_for('usuarios.admin_users'))

    roles = Rol.query.all()
    return render_template('admin_user_form.html', action='Crear', user=None, roles=roles)


@usuarios_bp.route('/admin/users/edit/<string:id_usuario>', methods=['GET', 'POST'])
@role_required('a', 'admin')  # ✅ cambio mínimo aquí
def admin_edit_user(id_usuario):
    user = Usuario.query.get_or_404(id_usuario)

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        new_password = request.form.get('password', '').strip()
        role = request.form.get('role')
        direccion_db = request.form.get('direccion', '').strip() or ''

        other = Usuario.query.filter(Usuario.correo == correo, Usuario.id_usuario != id_usuario).first()
        if other:
            flash('El correo ya está en uso por otro usuario', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)

        user.nombre = nombre
        user.correo = correo
        user.direccion = direccion_db

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
            flash(f'Error actualizando usuario: {e}', 'danger')
            roles = Rol.query.all()
            return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)

        flash('Usuario actualizado', 'success')
        return redirect(url_for('usuarios.admin_users'))

    roles = Rol.query.all()
    return render_template('admin_user_form.html', action='Editar', user=user, roles=roles)


@usuarios_bp.route('/admin/users/delete/<string:id_usuario>', methods=['POST'])
@role_required('a', 'admin')  # ✅ cambio mínimo aquí
def admin_delete_user(id_usuario):
    if id_usuario == session.get('username'):
        flash('No puedes eliminarte a ti mismo', 'warning')
        return redirect(url_for('usuarios.admin_users'))

    u = Usuario.query.get(id_usuario)
    if u:
        db.session.delete(u)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Error eliminando usuario: {e}', 'danger')
            return redirect(url_for('usuarios.admin_users'))
        flash('Usuario eliminado', 'success')
    else:
        flash('Usuario no encontrado', 'danger')

    return redirect(url_for('usuarios.admin_users'))


# -----------------------
# Crear tablas, roles y admin por defecto
# -----------------------
def create_default_data():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creando tablas: {e}")
        return

    try:
        rol_admin = find_or_create_role(db, Rol, 'admin')
        rol_user = find_or_create_role(db, Rol, 'user')
    except Exception as e:
        print(f"Error creando roles por defecto: {e}")
        return

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
            u.set_password('admin123')
            db.session.add(u)
            db.session.commit()
            print("✅ Usuario admin creado (user=admin, pass=admin123)")
    except Exception as e:
        db.session.rollback()
        print(f"Error creando usuario admin por defecto: {e}")
