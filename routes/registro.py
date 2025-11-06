# routes/registro.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import Usuario, Rol
from decorators import find_or_create_role
from flask_login import login_user
from werkzeug.security import generate_password_hash, check_password_hash

registro_bp = Blueprint('registro', __name__)

@registro_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_usuario = request.form['id_usuario'].strip()
        nombre = request.form['nombre'].strip()
        correo = request.form['correo'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']
        direccion = request.form.get('direccion', '').strip()

        # Validaciones básicas
        if password != confirm:
            flash('⚠️ Las contraseñas no coinciden', 'danger')
            return render_template('register.html')

        if Usuario.query.filter_by(id_usuario=id_usuario).first():
            flash('⚠️ El ID de usuario ya está registrado', 'danger')
            return render_template('register.html')

        if correo and Usuario.query.filter_by(correo=correo).first():
            flash('⚠️ El correo ya está registrado', 'danger')
            return render_template('register.html')

        # Crear o buscar rol 'user'
        rol_user = find_or_create_role(db, Rol, 'user')
        if not rol_user:
            flash('❌ Error creando rol de usuario', 'danger')
            return render_template('register.html')

        # Crear usuario
        direccion_db = direccion if direccion else ''
        nuevo_usuario = Usuario(
            id_usuario=id_usuario,
            nombre=nombre,
            correo=correo,
            direccion=direccion_db,
            id_rol=rol_user.id_rol
        )
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        try:
            db.session.commit()
            flash('✅ Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('registro.login'))  # correcto con tu blueprint
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al guardar el usuario: {e}', 'danger')
            return render_template('register.html')

    return render_template('register.html')



@registro_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = Usuario.query.filter_by(id_usuario=request.form['id_usuario']).first()

        if usuario and check_password_hash(usuario.contrasena, request.form['contrasena']):
            login_user(usuario)

            # 🔥 IMPORTANTE: Guardar el rol en la sesión
            session["role"] = usuario.id_rol 
            session["user_id"] = usuario.id_usuario

            flash("Inicio de sesión exitoso", "success")
            return redirect(url_for('home.index'))  # o la ruta que uses para el inicio
        else:
            flash("Usuario o contraseña incorrectos", "danger")

    return render_template('login.html')
