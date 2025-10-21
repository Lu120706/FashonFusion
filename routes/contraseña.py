from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Message
from itsdangerous import SignatureExpired
from ..models import Usuario  # importa tu modelo de usuario
from ..extensions import db, mail, s  # objetos globales creados en otro archivo

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
            flash('No existe un usuario con ese correo', 'danger')
            return render_template('forgot_password.html')

        # Generar token
        token = s.dumps(email, salt='reset-salt')
        link = url_for('contraseña.reset_password', token=token, _external=True)

        # Enviar correo
        msg = Message('Recupera tu contraseña',
                      sender=mail.sender,
                      recipients=[email])
        msg.body = f'Usa este enlace para resetear tu contraseña: {link}'
        try:
            mail.send(msg)
        except Exception as e:
            flash(f'Error enviando correo: {e}', 'danger')
            return render_template('forgot_password.html')

        flash('Se envió un enlace a tu correo para recuperar la contraseña.', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')


@contraseña_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-salt', max_age=3600)  # válido 1 hora
    except SignatureExpired:
        flash('El enlace expiró, solicita uno nuevo.', 'danger')
        return redirect(url_for('contraseña.forgot_password'))

    if request.method == 'POST':
        new_password = request.form['password']
        confirm = request.form['confirm_password']

        if new_password != confirm:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('reset_password.html', token=token)

        user = Usuario.query.filter_by(correo=email).first()
        if not user:
            flash('Usuario no encontrado', 'danger')
            return redirect(url_for('contraseña.forgot_password'))

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
