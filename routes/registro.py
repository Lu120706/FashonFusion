# routes/registro.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Usuario
from decorators import find_or_create_role  # si lo tienes en otro archivo, ajusta la ruta

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

        if password != confirm:
            flash('⚠️ Las contraseñas no coinciden', 'danger')
            return render_template('register.html')

        if Usuario.query.filter_by(id_usuario=id_usuario).first():
            flash('⚠️ El ID de usuario ya está registrado', 'danger')
            return render_template('register.html')

        if correo and Usuario.query.filter_by(correo=correo).first():
            flash('⚠️ El correo ya está registrado', 'danger')
            return render_template('register.html')

        # Asegurar que exista el rol 'user'
        rol_user = find_or_create_role('user')
        if not rol_user:
            flash('❌ Error creando rol de usuario', 'danger')
            return render_template('register.html')

        direccion_db = direccion if direccion is not None else ''

        u = Usuario(
            id_usuario=id_usuario,
            nombre=nombre,
            correo=correo,
            direccion=direccion_db,
            id_rol=rol_user.id_rol
        )
        u.set_password(password)

        db.session.add(u)
        try:
            db.session.commit()
            flash('✅ Registro exitoso. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login.login'))  # 👈 importante: cambiará cuando login tenga su propio blueprint
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al guardar el usuario: {e}', 'danger')
            return render_template('register.html')

    return render_template('register.html')