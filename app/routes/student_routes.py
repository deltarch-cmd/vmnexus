import logging, base64
from flask import Blueprint, render_template, redirect, request, url_for, flash, session
from functools import wraps

import app.guacamole as guacamole

from app.controllers import usuario_controller, asignatura_controller, laboratorio_controller, virtual_machines_controller

# Import the appropiate configuration
from app.config import Config
# from app.configUni import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

student_bp = Blueprint('student_bp', __name__, url_prefix='/alumno')

# Wrapper to check if the user is logged in
def check_logged_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_user') is None:
            flash('Por favor inicie sesión', 'info')
            return redirect(url_for('main_bp.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# home page
@student_bp.route('/home', methods=['GET'])
@check_logged_user
def home():
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario debe estar logueado por el wrapper"

    try:
        user = usuario_controller.get_usuario_by_id(logged_user['id'])
        if user is None:
            flash('Ha habido un error obteniendo la información, por favor inténtelo de nuevo más tarde', 'danger')
            return redirect(url_for('main_bp.login'))
    except Exception as e:
        flash(f'Error al obtener la información del usuario: {e}', 'danger')
        return redirect(url_for('main_bp.login'))

    if user.first_login:
        flash('Bienvenido a la plataforma, por favor actualice su contraseña', 'info')
        return redirect(url_for('main_bp.update_password', user_id=user.id))

    asignaturas = [matricula.asignatura.serialize() for matricula in user.matriculas]

    return render_template('student_home.html', current_user=user.serialize(), asignaturas=asignaturas)


# Asignaturas
@student_bp.route('/asignatura/<int:asignatura_id>', methods=['GET'])
@check_logged_user
def labs_asignatura(asignatura_id):
    """
    Renderiza la página de laboratorios de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Página de laboratorios de la asignatura
    """
    asignatura = asignatura_controller.get_asignatura_by_id(asignatura_id)
    if asignatura is None:
        flash('Ha habido un error con su solicitud, inténtelo de nuevo más tarde', 'danger')
        return redirect(url_for('student_bp.home'))

    laboratorios = [laboratorio.serialize() for laboratorio in asignatura.laboratorios]

    return render_template(
        'student_laboratorios.html',
        current_user=session["logged_user"],
        asignatura=asignatura,
        laboratorios=laboratorios
    )

# Laboratorios
@student_bp.route('/asignatura/<int:asignatura_id>/laboratorio/<int:laboratorio_id>', methods=['GET'])
@check_logged_user
def lab_content(asignatura_id, laboratorio_id):
    """
    Renderiza el contenido de un laboratorio

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :param laboratorio_id: ID del laboratorio
    :type laboratorio_id: int

    :return: Página de contenido del laboratorio o redirección a la página de laboratorios de la asignatura
    """
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario debe estar logueado por el wrapper"

    laboratorio = laboratorio_controller.get_laboratorio_by_id(laboratorio_id)

    if laboratorio is None:
        flash('Ha habido un error con su solicitud, inténtelo de nuevo más tarde', 'danger')
        return redirect(url_for('student_bp.labs_asignatura', asignatura_id=asignatura_id))

    try:
        guacamole_token = guacamole.get_guacamole_token()
    except ValueError as e:
        flash(f"Error al obtener el token de Guacamole: {e}", "danger")
        return redirect(url_for('student_bp.labs_asignatura', asignatura_id=asignatura_id))

    # Get the user's VM for that subject
    virtual_machines = virtual_machines_controller.get_virtual_machine_by_asignatura(asignatura_id)
    user_vms = [vm for vm in virtual_machines if vm.user_id == logged_user['id']]

    guacamole_url = ""
    if user_vms:
        connection_id = user_vms[0].guacamole_connection_id # Asume que solo hay una VM por usuario

        if connection_id is not None:
            # La conexión de Guacamole está compuesta de:
            #   - ID de la conexión
            #   - "c" o "g", dependiendo si se refiere a una conexión o un grupo
            #   - El tipo de sistema de autenticación (en este caso, mysql)
            # Cada valor está separado por \0

            connection_string = f"{connection_id}\0c\0{Config.GUACAMOLE.DATABASE_TYPE}"
            connection_base64 = base64.b64encode(connection_string.encode()).decode()

            guacamole_url = f"{Config.GUACAMOLE.BASE_URL}/#/client/{connection_base64}?token={guacamole_token}"

        else:
            logger.warning(f"No se ha encontrado la conexión de Guacamole para el usuario {logged_user['id']} con la máquina virtual {user_vms[0].nombre}")
            flash("No se ha encontrado la conexión de Guacamole para su máquina virtual", "warning")

    logger.info(f"URL de Guacamole: {guacamole_url}")

    # El PDF se debe encontrar en la carpeta static/flask_uploads/
    ## Esto se debe a que Flask carga los archivos en función de endpoints, y no de rutas en el sistema de archivos
    pdf_url = f"/{laboratorio.pdf_url.split('/', 1)[-1] if laboratorio.pdf_url else None}"
    asignatura = asignatura_controller.get_asignatura_by_id(asignatura_id)

    return render_template(
        'student_lab_content.html',
        current_user=logged_user,
        asignatura=asignatura,
        laboratorio=laboratorio,
        pdf_url=pdf_url,
        guacamole_url=guacamole_url
    )
