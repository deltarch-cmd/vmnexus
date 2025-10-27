from flask import Blueprint, render_template, redirect, url_for, request, flash, session

from app.controllers import usuario_controller
from app.utils.orphaned_files_cleanup import clean_orphaned_files
from app.utils.populate_database import manage_data

import app.controllers.usuario_controller as user_controller

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main_bp.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gestiona el inicio de sesión de un usuario

    - **GET**: Renderiza la pantalla de inicio de sesión
    - **POST**: Autentica al usuario

    Si el usuario es autenticado con éxito:
    - Admin: Redirige al dashboard del administrador
    - Estudiante: Redirige al home del estudiante

    :return: Página de inicio de sesión o redirección basada en el rol del usuario
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username contains an '@' character
        if '@' not in username:
            user = user_controller.get_usuario_by_nombre_usuario(username)
            if not user:
                flash("Invalid credentials", "danger")
                return redirect(url_for('main_bp.login'))
            username = user.email

        # Authenticate the user
        try:
            user = user_controller.authenticate_user(username, password)
            if not user:
                flash("Invalid credentials", "danger")
                return redirect(url_for('main_bp.login'))
        except Exception as e:
            flash(str(e), "danger")
            return redirect(url_for('main_bp.login'))

        session['logged_user'] = user.serialize()
        if user.is_admin:
            return redirect(url_for('admin_bp.dashboard'))
        else:
            return redirect(url_for('student_bp.home'))

    # Data loading
    manage_data(0)
    clean_orphaned_files()

    return render_template('login.html', show_footer=True, current_user=None)

# Update password
@main_bp.route('/update_password/<int:user_id>', methods=['GET', 'POST'])
def update_password(user_id):
    logged_user = session.get('logged_user')

    if logged_user and logged_user['id'] != user_id:
        flash('No tiene permiso para acceder a esta página', 'danger')
        return redirect(url_for('student_bp.home'))

    user = usuario_controller.get_usuario_by_id(user_id)
    if not user:
        flash('No se ha encontrado el usuario, por favor inténtelo de nuevo más tarde', 'danger')
        return redirect(url_for('student_bp.home'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not user.check_password(old_password):
            flash('La contraseña actual no es correcta', 'danger')
            return render_template('update_password.html', current_user=user.serialize())

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('update_password.html', current_user=user.serialize())

        usuario_controller.update_user_password(user.id, old_password, password)

        flash('Contraseña actualizada exitosamente', 'success')
        return redirect(url_for('main_bp.login'))

    return render_template('update_password.html', current_user=user.serialize(), user_id=user.id)

@main_bp.route('/logout')
def logout():
    session.pop('logged_user', None)
    session.clear()
    return redirect(url_for('main_bp.login'))
