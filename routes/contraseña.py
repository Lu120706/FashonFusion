from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Message
from itsdangerous import SignatureExpired
from models import Usuario
from extensions import db, mail, get_serializer

# Crear blueprint
contraseña_bp = Blueprint('contraseña', __name__)

# -----------------------
# Recuperación de contraseña
# -----------------------
@contraseña_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = Usuario.query.filter_by(correo=email).first()

        if not user:
            flash('No existe un usuario con ese correo.', 'danger')
            return render_template('forgot_password.html')

        # Generar token (usar el mismo salt en ambos métodos)
        s = get_serializer()
        salt = "password-reset-salt"
        token = s.dumps(user.correo, salt=salt)
        link = url_for('contraseña.reset_password', token=token, _external=True)

        # Enviar correo
        msg = Message(
            subject='Recupera tu contraseña',
            sender='tu_correo@gmail.com',  # ⚠️ Reemplaza con tu correo configurado
            recipients=[email],
            body=f'Usa este enlace para restablecer tu contraseña: {link}'
        )

        try:
            mail.send(msg)
            flash('Se envió un enlace a tu correo para recuperar la contraseña.', 'info')
        except Exception as e:
            flash(f'Error enviando correo: {e}', 'danger')
            return render_template('forgot_password.html')

        # Redirige al login (ajusta si tu login está en otro blueprint)
        return redirect(url_for('registro.login'))

    return render_template('forgot_password.html')


# -----------------------
# Restablecer contraseña
# -----------------------
@contraseña_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    s = get_serializer()
    salt = "password-reset-salt"

    try:
        email = s.loads(token, salt=salt, max_age=3600)  # válido 1 hora
    except SignatureExpired:
        flash('El enlace expiró, solicita uno nuevo.', 'danger')
        return redirect(url_for('contraseña.forgot_password'))
    except Exception:
        flash('El enlace no es válido o fue alterado.', 'danger')
        return redirect(url_for('contraseña.forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm = request.form['confirm_password']

        if new_password != confirm:
            flash('Las contraseñas no coinciden.', 'danger')
            return render_template('reset_password.html', token=token)

        user = Usuario.query.filter_by(correo=email).first()
        if not user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('contraseña.forgot_password'))

        user.set_password(new_password)

        try:
            db.session.commit()
            flash('Tu contraseña fue actualizada. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error actualizando contraseña: {e}', 'danger')
            return render_template('reset_password.html', token=token)

    return render_template('reset_password.html', token=token)
