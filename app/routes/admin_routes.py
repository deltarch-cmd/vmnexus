import os, uuid, logging
from flask import Blueprint, render_template, redirect, session, url_for, request, flash, current_app
import time
from time import sleep
from functools import wraps
from werkzeug.utils import secure_filename
from datetime import datetime

import app.proxmox as proxmox
import app.guacamole as guacamole
from app.controllers import horario_controller, usuario_controller, asignatura_controller, matricula_controller, virtual_machines_controller

from app.utils.tasks import reschedule_virtual_machines_tasks

# Import the appropiate configuration
from app.config import Config
# from app.configUni import Config

# Constants
DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
BYTES_IN_GIB = 1073741824

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define other Proxmox specific names
proxmox_node = Config.PROXMOX.NODE_NAME

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        logged_user = session.get('logged_user')
        if not logged_user or logged_user['is_admin'] != True:
            flash("No tienes permisos para acceder a esta página", "warning")
            return redirect(url_for('main_bp.login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def check_proxmox_connection(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('proxmox_connected') is not True:
            try:
                proxmox.get_proxmox_conn()
                session['proxmox_connected'] = True

            except ConnectionError as e:
                flash(f"Error connecting to Proxmox: {e}", "warning")
                return redirect(url_for('admin_bp.dashboard'))

        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# Función para manejar la subida de archivos
def handle_uploads(file_data):
    """
    Maneja la subida de archivos PDF de los laboratorios

    :param file_data: Diccionario con los datos de los laboratorios
    :type file_data: dict

    :return: Lista de URLs de los archivos subidos
    :rtype: list[str]
    """
    labs = file_data['labs']
    lab_files = file_data['lab-files']

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    pdf_urls_list = [] # List of URLs to be stored in the database

    for i, lab in enumerate(labs):
        pdf_file = lab_files[i] if lab_files[i].filename != '' else None

        if pdf_file is None:
            logger.warning(f"No file to save for lab {lab}")
            pdf_urls_list.append(None) # Add None to the list
            continue

        filename_sanitized = secure_filename(pdf_file.filename) # Sanitize the filename
        filename_sanitized = filename_sanitized.split('.')[0] # Remove the extension
        timestamp = int(datetime.now().timestamp()) # Get the current timestamp
        uuid_str = uuid.uuid4().hex[:8] # Generate a UUID

        lab = lab.replace(' ', '_') # Replace spaces with underscores
        filename = f"{filename_sanitized}_{lab}_{timestamp}_{uuid_str}.pdf"

        pdf_file.save(os.path.join(upload_dir, filename))
        pdf_urls_list.append(f"{Config.FLASK.UPLOAD_FOLDER}/{filename}")

        logger.info(f"Saved file {filename} to {upload_dir}")

    return pdf_urls_list

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    proxmox_connected = False # Used to display information about the connection to Proxmox
    guacamole_connected = False
    try:
        proxmox.get_proxmox_conn()
        proxmox_connected = True

        guacamole.get_guacamole_token()
        guacamole_connected = True

    except ConnectionError as e:
        logger.error(f"Error connecting to Proxmox: {e}\n")
        flash(f"No ha sido posible conectarse al servidor de Proxmox", "warning")
    except guacamole.GuacamoleError as e:
        logger.error(f"Error connecting to Guacamole: {e}\n")
        flash(f"No ha sido posible ocnectarse al servidor de Guacamole", "warning")
    finally:
        # Se guarda el estado de la conexión en la sesión
        session['proxmox_connected'] = proxmox_connected
        session['guacamole_connected'] = guacamole_connected

    logger.info(f"Connected to Proxmox: {proxmox_connected}")

    return render_template(
        'admin_dashboard.html',
        proxmox_connected=session['proxmox_connected'],
        guacamole_connected=session['guacamole_connected'],
        current_user=session['logged_user']
    )

# Rutas de gestión
@admin_bp.route('/gestion_asignaturas', methods=['GET'])
@admin_required
def gestion_asignaturas():
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    asignaturas = asignatura_controller.get_asignatura_by_profesor(logged_user['id'])
    list_asignaturas = [
        {
            **asignatura.serialize(),
            'laboratorios': [lab.serialize(with_pdf_name=True) for lab in asignatura.laboratorios]
        }
        for asignatura in asignaturas
    ]

    return render_template(
        'admin_gestion_asignaturas.html',
        asignaturas=list_asignaturas, current_user=logged_user
    )

@admin_bp.route('/gestion_usuarios', methods=['GET'])
@admin_required
def gestion_usuarios():
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    usuarios = usuario_controller.get_all_usuarios()
    list_usuarios = [usuario.serialize() for usuario in usuarios]

    return render_template(
        'admin_gestion_usuarios.html',
        usuarios=list_usuarios, current_user=logged_user
    )

@admin_bp.route('/gestion_maquinas', methods=['GET'])
@admin_required
def gestion_maquinas():
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    if session.get('proxmox_connected') is not True:
        try:
            _ = proxmox.get_proxmox_conn()
            session['proxmox_connected'] = True

        except ConnectionError as e:
            flash(f"Error connecting to Proxmox: {e}", "warning")
            return redirect(url_for('admin_bp.dashboard'))

    print("Connected to Proxmox")

    # Get the list of virtual machines in our database
    database_vms = [vm.serialize() for vm in virtual_machines_controller.get_all_virtual_machines()]
    database_vm_ids = [vm['proxmox_id'] for vm in database_vms]

    # Get the list of virtual machines in Proxmox
    proxmox_vms = proxmox.get_all_vms_serialized()

    # Asignaturas sin máquinas base
    asignaturas_sin_maquinas_base = asignatura_controller.get_asignaturas_without_virtual_machines()
    asignaturas_sin_maquinas_base = [asignatura.serialize() for asignatura in asignaturas_sin_maquinas_base]

    # Divide the virtual machines in Proxmox in two lists: registered and unregistered
    registered_vms = []
    unregistered_vms = []

    for vm in proxmox_vms:
        if vm['id'] in database_vm_ids:
            if database_vms[database_vm_ids.index(vm['id'])]['is_base_vm']:
                registered_vms.append(vm)
        else:
            unregistered_vms.append(vm)

    registered_vms.sort(key=lambda x: x['id'])
    unregistered_vms.sort(key=lambda x: x['id'])

    return render_template(
        'admin_gestion_maquinas.html',
        registered_vms=registered_vms,
        unregistered_vms=unregistered_vms,
        asignaturas=asignaturas_sin_maquinas_base,
        current_user=logged_user
    )

## Gestion de asignaturas
### Funciones de ayuda para modularizar los métodos
def validate_lab_data(lab_ids, lab_names):
    if not all(lab_id.isdigit() for lab_id in lab_ids if lab_id):
        return "Error al subir los archivos. La lista de ID's no contiene solo números"

    if len(lab_names) != len(lab_ids):
        return "Error al subir los archivos. La listas de nombres y de ID's no son iguales."

    return None # No errors

# Crea la lista de datos de laboratorios pasada a los controladores
def zip_lab_data(lab_ids, lab_names, pdf_url_list):
    return [
        {
            'id': int(lab_id) if lab_id != '' else '',
            'nombre': lab_name,
            'pdf_url': pdf_url
        }
        for lab_id, lab_name, pdf_url in zip(lab_ids, lab_names, pdf_url_list)
    ]

def zip_horario_data(horarios_ids, horarios_dias, horarios_horas_inicio, horarios_horas_fin):
    return [
        {
            'id': int(horario_id) if horario_id != '' else '',
            'dia': dia,
            'hora_inicio': hora_inicio,
            'hora_fin': hora_fin
        }
        for horario_id, dia, hora_inicio, hora_fin in zip(horarios_ids, horarios_dias, horarios_horas_inicio, horarios_horas_fin)
    ]

# Maneja la acción del formulario de asignaturas
def handle_form_action_asignatura(logged_user, action, asignatura=None):
    # Datos asignatura
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')

    # Datos laboratorios
    lab_ids = request.form.getlist('lab-ids[]')
    lab_names = request.form.getlist('labs[]')
    lab_pdf_files = request.files.getlist('lab-files[]')

    # Datos matriculas / alumnos
    alumnos_ids = request.form.getlist('alumnos-ids[]')
    alumnos_ids = set(map(int, alumnos_ids)) # Convertir a conjunto para eliminar duplicados

    # Datos horarios
    horarios_ids = request.form.getlist('horario-ids[]')
    horarios_dias = request.form.getlist('dias[]')
    horarios_horas_inicio = request.form.getlist('horas-inicio[]')
    horarios_horas_fin = request.form.getlist('horas-fin[]')

    error_message = validate_lab_data(lab_ids, lab_names)
    if error_message:
        flash(error_message, "danger")
        return redirect(url_for('admin_bp.crear_asignatura'))

    file_data = {
        'labs': lab_names,
        'lab-files': lab_pdf_files
    }
    pdf_url_list = handle_uploads(file_data)

    labs_data = zip_lab_data(lab_ids, lab_names, pdf_url_list)
    horarios_data = zip_horario_data(horarios_ids, horarios_dias, horarios_horas_inicio, horarios_horas_fin)

    try:
        if action == "create":
            new_asig = asignatura_controller.create_asignatura_with_entidades(
                nombre,
                logged_user['id'], # Asume que el usuario es el profesor
                descripcion,
                labs_data,
                alumnos_ids,
                horarios_data
            )
            reschedule_virtual_machines_tasks(new_asig.id)
            flash("Asignatura creada correctamente", "success")

        elif action == "edit" and asignatura is not None:
            asignatura_controller.update_asignatura(
                asignatura.id,
                nombre,
                descripcion,
                labs_data,
                alumnos_ids,
                horarios_data
            )
            reschedule_virtual_machines_tasks(asignatura.id)
            flash("Asignatura actualizada correctamente", "success")

    except asignatura_controller.AsignaturaException as e:
        flash(f"Error al crear la asignatura: {e}", "danger")
    
    return redirect(url_for('admin_bp.gestion_asignaturas'))

@admin_bp.route('/asignatura', methods=['GET', 'POST'])
@admin_required
def crear_asignatura():
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    if request.method == 'POST':
        return handle_form_action_asignatura(logged_user, "create")

    # Se obtienen los alumnos no matriculados (en sí serán todos)
    alumnos_no_matriculados = usuario_controller.get_all_usuarios()

    return render_template(
        "admin_formulario_asignatura.html",
        alumnos_no_matriculados=alumnos_no_matriculados,
        current_user=logged_user
    )

@admin_bp.route('/asignatura/<int:id_asignatura>/edit', methods=['GET', 'POST'])
@admin_required
def editar_asignatura(id_asignatura):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    asignatura = asignatura_controller.get_asignatura_by_id(id_asignatura)
    if asignatura is None:
        flash("No se ha encontrado la asignatura", "warning")
        return redirect(url_for('admin_bp.gestion_asignaturas'))

    if request.method == 'POST':
        return handle_form_action_asignatura(logged_user, "edit", asignatura)

    # Se serializa la asignatura y sus laboratorios
    list_asignaturas = {
        **asignatura.serialize(),
        'laboratorios': [lab.serialize(with_pdf_name=True) for lab in asignatura.laboratorios]
    }

    # Se obtienen los alumnos matriculados en la asignatura
    alumnos_matriculados = matricula_controller.get_objetos_alumnos_matriculados(asignatura.id)

    # Se obtiene una lista con los alumnos no matriculados
    alumnos_no_matriculados = matricula_controller.get_objetos_alumnos_no_matriculados(asignatura.id)

    # Horarios de la asignatura
    horarios = horario_controller.get_all_horarios_by_asignatura(asignatura.id)

    return render_template(
        'admin_formulario_asignatura.html',
        asignatura=list_asignaturas,
        alumnos_matriculados=alumnos_matriculados,
        alumnos_no_matriculados=alumnos_no_matriculados,
        horarios=horarios,
        dias=DIAS_SEMANA,
        current_user=logged_user
    )

@admin_bp.route('/asignatura/<int:id_asignatura>/delete', methods=['GET'])
@admin_required
def borrar_asignatura(id_asignatura):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    asignatura = asignatura_controller.get_asignatura_by_id(id_asignatura)
    if asignatura is None:
        flash("No se ha encontrado la asignatura", "warning")
        return redirect(url_for('admin_bp.gestion_asignaturas'))

    try:
        associated_vms = virtual_machines_controller.get_virtual_machine_by_asignatura(asignatura.id)
        base_vm_id = [vm.proxmox_id for vm in associated_vms if vm.is_base_vm]
        error_msg = None

        if base_vm_id:
            error_msg = deregister_maquina_virtual(base_vm_id[0])

        if error_msg:
            flash(error_msg, "danger")
            return redirect(url_for('admin_bp.gestion_asignaturas'))

        asignatura_controller.delete_asignatura(asignatura.id)
        flash("Asignatura eliminada correctamente", "success")
        return redirect(url_for('admin_bp.gestion_asignaturas'))

    except ValueError as e:
        flash(f"El ID de la asignatura no es válido: {e}", "danger")

    except asignatura_controller.AsignaturaException as e:
        flash(f"Ha ocurrido un error al eliminar la asignatura {e}", "danger")

    except Exception as e:
        flash(f"Ha ocurrido un error al eliminar la asignatura {e}", "danger")
    
    return redirect(url_for('admin_bp.gestion_asignaturas'))

def handle_form_action_usuario(action, usuario=None):
    # Datos usuario
    nombre = request.form.get('nombre')
    email = request.form.get('email')
    rol = request.form.get('rol')

    # Datos matriculas
    asignaturas_ids = request.form.getlist('asignaturas-ids[]')
    asignaturas_ids = set(map(int, asignaturas_ids)) # Convertir a conjunto para eliminar duplicados

    try:
        if action == "create":
            password = request.form.get('password')
            password_confirm = request.form.get('password_confirm')

            if password != password_confirm:
                flash("Las contraseñas no coinciden", "danger")
                return redirect(url_for('admin_bp.crear_usuario'))

            usuario_controller.create_user_with_matriculas(
                nombre,
                email,
                password,
                asignaturas_ids,
                rol == 'administrador'
            )
            flash("Usuario creado correctamente", "success")

        elif action == "edit" and usuario is not None:
            usuario_controller.update_usuario_with_matriculas(
                usuario.id,
                nombre,
                email,
                asignaturas_ids,
                rol == 'administrador'
            )
            flash("Usuario actualizado correctamente", "success")

    except ValueError as e:
        flash(f"Error al crear el usuario: {e}", "danger")

    return redirect(url_for('admin_bp.gestion_usuarios'))

@admin_bp.route('/usuario', methods=['GET', 'POST'])
@admin_required
def crear_usuario():
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    if request.method == 'POST':
        return handle_form_action_usuario("create")

    asignaturas_no_matriculado = asignatura_controller.get_all_asignaturas()

    return render_template(
        "admin_formulario_usuario.html",
        asignaturas_no_matriculado=asignaturas_no_matriculado,
        current_user=logged_user
    )

@admin_bp.route('/usuario/<int:id_usuario>/edit', methods=['GET', 'POST'])
@admin_required
def editar_usuario(id_usuario):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    usuario = usuario_controller.get_usuario_by_id(id_usuario)
    if usuario is None:
        flash("No se ha encontrado el usuario", "warning")
        return redirect(url_for('admin_bp.gestion_usuarios'))

    if request.method == 'POST':
        return handle_form_action_usuario("edit", usuario)

    asignaturas_matriculado = matricula_controller.get_objetos_asignaturas_matriculadas(usuario.id)

    asignaturas_no_matriculado = matricula_controller.get_objectos_asignaturas_no_matriculadas(usuario.id)

    return render_template(
        'admin_formulario_usuario.html',
        usuario=usuario.serialize(),
        asignaturas_matriculado=asignaturas_matriculado,
        asignaturas_no_matriculado=asignaturas_no_matriculado,
        current_user=logged_user
    )

@admin_bp.route('/usuario/<int:id_usuario>/delete', methods=['GET'])
@admin_required
def borrar_usuario(id_usuario):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    usuario = usuario_controller.get_usuario_by_id(id_usuario)
    if usuario is None:
        flash("No se ha encontrado el usuario", "warning")

    else:
        usuario_controller.delete_usuario(usuario.id)
        flash("Usuario eliminado correctamente", "success")

    return redirect(url_for('admin_bp.gestion_usuarios'))

# Gestion de máquinas
## Funciones de ayuda para modularizar los métodos
def deregister_maquina_virtual(proxmox_id):
    """
    Este método borra la máquina virtual la base de datos, no de Proxmox. Además,
    también da de baja todos los clones si existen.
    """
    try:
        vm = virtual_machines_controller.get_virtual_machine_by_id(proxmox_id)
        if vm is None:
            return f"La VM {proxmox_id} no se encuentra en la base de datos"

        if vm.is_base_vm:
            # Al ser una máquina base, se obtienen los clones y se dan de baja
            clones = virtual_machines_controller.get_clones_of_virtual_machine(proxmox_id)
            token = guacamole.get_guacamole_token()
            for clone in clones:
                try:
                    if clone.guacamole_connection_id:
                        guacamole.delete_guacamole_connection(token, clone.guacamole_connection_id)

                    virtual_machines_controller.delete_virtual_machine(clone.proxmox_id)

                except guacamole.GuacamoleError as e:
                        return f"Error al dar de baja el clon {clone.proxmox_id} en Guacamole: {e}"
                except Exception as e:
                    return f"Error al dar de baja el clon {clone.proxmox_id}: {e}"

        # Se elimina la máquina virtual
        virtual_machines_controller.delete_virtual_machine(proxmox_id)

    except ValueError as e:
        return f"El ID de la VM no es válido: {e}"

    except Exception as e:
        return f"Error al dar de baja la VM: {e}"

    return None # No errors

## Operaciones que no requieren conexión con Proxmox directamente
@admin_bp.route('/virtual_machines/<int:proxmox_id>/desregistrar', methods=['GET'])
@admin_required
def dar_de_baja_maquina_virtual(proxmox_id):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    error_message = deregister_maquina_virtual(proxmox_id)
    if error_message:
        flash(error_message, "danger")
    else:
        flash(f"VM {proxmox_id} dada de baja correctamente", "success")

    return redirect(url_for('admin_bp.gestion_maquinas'))

## Operaciones con Proxmox
@admin_bp.route('/virtual_machines/proxmox/<int:proxmox_id>/registrar', methods=['POST'])
@admin_required
@check_proxmox_connection
def registrar_maquina_virtual(proxmox_id):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    try:
        proxmox_vm = proxmox.get_vm_by_id(proxmox_id)
        if proxmox_vm is None:
            flash(f"La VM {proxmox_id} no se encuentra en Proxmox", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        asignatura_id = request.form.get('asignatura')
        vnc_username = request.form.get('vnc-username')
        vnc_password = request.form.get('vnc-password')
        vnc_repassword = request.form.get('vnc-repassword')

        if vnc_password != vnc_repassword:
            flash("Las contraseñas VNC no coinciden", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        if not asignatura_id or not asignatura_id.isdigit():
            flash("Ha habido un error al obtener el ID de la asignatura", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        virtual_machines_controller.create_virtual_machine(
            proxmox_id=proxmox_id,
            name=proxmox_vm['name'],
            user_id=logged_user['id'],
            asignatura_id=int(asignatura_id),
            vnc_username=vnc_username,
            vnc_password=vnc_password,
            is_base=True
        )
        flash(f"VM {proxmox_id} registrada correctamente", "success")

    except Exception as e:
        flash(f"Error al registrar la VM: {e}", "danger")

    return redirect(url_for('admin_bp.gestion_maquinas'))

@admin_bp.route('/virtual_machines/proxmox/<int:proxmox_id>/edit', methods=['GET', 'POST'])
@admin_required
def editar_maquina_virtual(proxmox_id):
    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    vm = proxmox.get_vm_serialized(proxmox_id)
    database_vm = virtual_machines_controller.get_virtual_machine_by_id(proxmox_id)

    vm_clone_list = virtual_machines_controller.get_clones_of_virtual_machine(proxmox_id)

    if request.method == 'POST':
        # Hay que obtener la lista de clones de la máquina virtual
        new_clone_list = request.form.getlist('clones[]')
        if not new_clone_list:
            flash("Hubo un error con su solicitud: no se encontraron clones de la máquina virtual", "warning")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        try:
            # Convertir la lista de clones en un diccionario
            ## Debido a que los usuarios pueden ser nulos, hay que realizar comprobaciones adicionales
            clone_dict = {}
            for x in new_clone_list:
                proxmox_id, user_id = x.split(':')
                if user_id in ['null', '-1']:
                    clone_dict[int(proxmox_id)] = None
                else:
                    clone_dict[int(proxmox_id)] = int(user_id)

            updates = [
                {
                    "proxmox_id": clone.proxmox_id,
                    "user_id": clone_dict[clone.proxmox_id]
                }
                for clone in vm_clone_list if clone_dict.get(clone.proxmox_id) is not None 
                and clone.user_id != clone_dict[clone.proxmox_id]
            ]
            virtual_machines_controller.bulk_update_virtual_machines(updates)

            flash(f"Clones actualizados correctamente", "success")

        except Exception as e:
            flash(f"Error al actualizar los clones de la máquina virtual: {e}", "danger")

        return redirect(url_for('admin_bp.gestion_maquinas'))

    if vm is None or database_vm is None:
        flash("No se ha encontrado la máquina virtual", "warning")
        return redirect(url_for('admin_bp.gestion_maquinas'))

    vm['maxdisk'] = vm['maxdisk'] // BYTES_IN_GIB # Convertir a GiB
    vm['maxmem'] = vm['maxmem'] // BYTES_IN_GIB # Convertir a GiB

    alumnos = matricula_controller.get_objetos_alumnos_matriculados(database_vm.asignatura_id)
    asignatura_relacionada = asignatura_controller.get_asignatura_by_id(database_vm.asignatura_id)

    clone_list = [vm.serialize() for vm in vm_clone_list]

    # Asociamos el usuario a cada clone
    for clone in clone_list:
        usuario_asignado = next((a.serialize() for a in alumnos if a.id == clone['user_id']), None)

        # Debido a que los clones pueden no tener un usuario asignado, hay que comprobar también si "realmente" el clon tiene un user_id
        if usuario_asignado is None and clone['user_id']:
            try: 
                # Se comprueba si el usuario existe en la base de datos
                usuario_controller.get_usuario_by_id(clone['user_id'])
            except ValueError as e:
                logger.error(f"Error al obtener el usuario asignado debido a que el ID no es un entero: {e}")
                flash(f"Error al obtener el usuario asignado: {e}", "danger")

            except Exception as e:
                logger.error(f"El clon {clone['proxmox_id']} tiene un usuario asignado que no existe: {e}")
                flash("Ha ocurrido un error inesperado al obtener el usuario asignado", "danger")

        # Se destaca que, si el usuario asignado es administrador,
        # no se mostrará en la lista de usuarios asignados, mostrando
        # en su lugar "Ningún alumno asignado"
        clone['user'] = usuario_asignado

    return render_template(
        'admin_formulario_maquina_virtual.html',
        proxmox_vm=vm,
        asignatura_relacionada=asignatura_relacionada,
        alumnos=alumnos,
        clones=clone_list,
        current_user=logged_user
    )

### Funciones de ayuda para modularizar el método de clonación
def validate_clone_data(proxmox_id, n_clones, new_starting_id, proxmox_vms_ids):
    if not isinstance(n_clones, int):
        if not n_clones.isdigit():
            return "El número de clones no es un número válido"

    if not isinstance(new_starting_id, int):
        if not new_starting_id.isdigit():
            return "El ID de inicio no es un número válido"

    n_clones = int(n_clones)
    new_starting_id = int(new_starting_id)
    needed_ids = [new_starting_id + i for i in range(n_clones)]

    logger.info(f"new_starting_id: {new_starting_id}")
    logger.info(f"Needed IDs: {needed_ids}")

    if any(vm_id in proxmox_vms_ids for vm_id in needed_ids):
        if n_clones > 1:
            error_msg = f"Algún ID del rango {new_starting_id} - {new_starting_id + n_clones-1} ya está en uso"
        else:
           error_msg =  f"El ID {new_starting_id} ya está en uso"

        return error_msg

    vm_a_clonar = proxmox.get_vm_by_id(proxmox_id)

    if vm_a_clonar is None:
        return f"La VM {proxmox_id} no se encuentra en Proxmox o en la base de datos"
    
    return vm_a_clonar

@admin_required
def store_clones_in_database(base_vm_obj, n_clones, new_starting_id):
    # Guardar la información de los clones en la base de datos
    try:
        logged_user = session.get('logged_user')
        assert logged_user is not None, "El usuario va a existir por el wrapper"

        alumnos_matriculados = matricula_controller.get_objetos_alumnos_matriculados(base_vm_obj.asignatura_id)

        alumnos_matriculados = list(
            filter(lambda x: not x.is_admin, alumnos_matriculados)
        )

        virtual_machines = virtual_machines_controller.get_all_virtual_machines()
        alumnos_sin_vm = list(
            filter(lambda alumno: not any(vm.user_id == alumno.id for vm in virtual_machines), alumnos_matriculados)
        )

        for i in range(int(n_clones)):
            alumno_id = logged_user['id']
            if i < len(alumnos_sin_vm): # Si hay alumnos sin VMs
                alumno_id = alumnos_sin_vm[i].id

            new_id = new_starting_id + i
            virtual_machines_controller.create_virtual_machine(
                proxmox_id=new_id,
                name=f"clone-{new_id}-{base_vm_obj.nombre}",
                user_id=alumno_id,
                asignatura_id=base_vm_obj.asignatura_id,
                vnc_username=base_vm_obj.vnc_username,
                vnc_password=base_vm_obj.get_vnc_password(),
                is_base=False,
                cloned_from=base_vm_obj.proxmox_id
            )

    except Exception as e:
        raise Exception(f"Error al crear los clones en la base de datos: {e}")

@admin_bp.route('/virtual_machines/proxmox/<int:proxmox_id>/clonar', methods=['POST'])
@admin_required
@check_proxmox_connection
def clonar_maquina_virtual(proxmox_id):
    """Clona una máquina virtual de Proxmox

    Esta ruta clona una máquina virtual de Proxmox, creando una o varias copias de la misma dependiendo de los datos del formulario.

    El formulario contiene los siguientes campos:
        - num-clones: Número de clones a crear
        - start-id: ID de inicio para los clones
        - create-connections: Checkbox para crear conexiones en Guacamole

    :param proxmox_id: ID de la máquina virtual a clonar
    :type proxmox_id: int

    :return: Redirige a la página de gestión de máquinas virtuales independientemente del resultado.
    """

    # Prueba de rendimiento: tiempo
    start_time = time.perf_counter()

    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    try:
        # Obtener los IDs de las máquinas virtuales en Proxmox
        proxmox_vms = proxmox.get_all_vms_serialized()
        proxmox_vms_ids = [vm['id'] for vm in proxmox_vms]

        n_clones = request.form.get('num-clones')
        new_starting_id = request.form.get('start-id')
        create_guacamole_conn = request.form.get('check-connections') == 'on'

        # Se obtiene la VM a clonar validando los datos
        vm_a_clonar = validate_clone_data(proxmox_id, n_clones, new_starting_id, proxmox_vms_ids)

        if isinstance(vm_a_clonar, str): 
            flash(vm_a_clonar, "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        # Se comprueba si la VM a clonar está en la base de datos
        database_vm = virtual_machines_controller.get_virtual_machine_by_id(proxmox_id)
        if database_vm is None:
            raise Exception(f"La VM {proxmox_id} no se encuentra en la base de datos")

        # Ya se validó que los datos se pueden convertir a enteros
        new_starting_id = int(new_starting_id)
        n_clones = int(n_clones)
        vm_disk_size = vm_a_clonar['maxdisk'] // BYTES_IN_GIB # Convertir a GiB

        flash("Clonando la VM, por favor espere...", "info")

        timeout = 180 if vm_disk_size > 30 else 120
        timeout = timeout * n_clones
        
        # Clonar la máquina virtual de Proxmox
        proxmox.clone_vm(
            vmid=proxmox_id,
            base_vm_name=vm_a_clonar['name'],
            new_starting_id=new_starting_id,
            number_of_clones=n_clones,
            timeout=timeout
        )

        # Se guarda la información de los clones en la base de datos
        store_clones_in_database(database_vm, n_clones, new_starting_id)

        # Se actualizan las operaciones en segundo plano para incluir las nuevas máquinas virtuales
        reschedule_virtual_machines_tasks(database_vm.asignatura_id)

        flash_message = "VM clonada correctamente"

        logger.info(f"Checkbox guacamole: {create_guacamole_conn}")
        if create_guacamole_conn:
            guaca_token = guacamole.get_guacamole_token()

            clones_ids = [new_starting_id + i for i in range(n_clones)]

            # Esta operación es muy costosa y es en la que más tiempo se tarda
            clones_ips = proxmox.get_virtual_machines_ip(clones_ids)
            clones_data = clones_ips.copy()

            for vm_id, vm_ip in clones_ips.items():
                logger.info(f"IP de VM {vm_id}: {vm_ip}")
                guacamole_conn_id = guacamole.create_guacamole_connection(
                    token=guaca_token,
                    virtual_machine_ip=vm_ip,
                    connection_name=f"clone-{vm_id}-{database_vm.nombre}",
                    virtual_machine_username=database_vm.vnc_username,
                    connection_password=database_vm.get_vnc_password()
                )
                clones_data[vm_id] = guacamole_conn_id

            # Se guardan los datos de las conexiones en la base de datos
            virtual_machines_controller.bulk_update_virtual_machines(
                [
                    {
                        "proxmox_id": vm_id,
                        "guacamole_connection_id": guaca_conn_id
                    }
                    for vm_id, guaca_conn_id in clones_data.items()
                ]
            )

            flash_message += " y conexiones de Guacamole creadas exitosamente"

        flash(flash_message, "success")

        elapsed_time = time.perf_counter() - start_time
        logger.info(f"\nTiempo total de la operación: {elapsed_time:.3f} segundos\n")

        return redirect(url_for('admin_bp.editar_maquina_virtual', proxmox_id=proxmox_id))

    except ValueError as e:
        flash(f"Error al obtener los datos del formulario: {e}", "danger")

    except guacamole.GuacamoleError as e:
        flash(f"Error al crear las conexiones de Guacamole: {e}", "danger")

    except proxmox.ProxmoxError as e:
        flash(f"Error al obtener los datos de las VM's de Proxmox: {e}", "danger")

    except Exception as e:
        flash(f"Error al realizar la operación: {e}", "danger")

    return redirect(url_for('admin_bp.gestion_maquinas'))

@admin_bp.route('/virtual_machines/proxmox/<int:proxmox_id>/eliminar', methods=['GET'])
@admin_required
@check_proxmox_connection
def eliminar_maquina_virtual(proxmox_id):
    try:
        proxmox_vm = proxmox.get_vm_by_id(proxmox_id)
        if proxmox_vm is None:
            flash(f"La VM {proxmox_id} no se encuentra en Proxmox", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        # Eliminar la máquina virtual de Proxmox
        proxmox.delete_vm(proxmox_id)
        sleep(1) # 1 second sleep to give the server time to delete the VM

        flash(f"VM {proxmox_id} eliminada correctamente", "success")

    except Exception as e:
        flash(f"Error al eliminar la VM: {e}", "danger")

    return redirect(url_for('admin_bp.gestion_maquinas'))

@admin_bp.route('/virtual_machines/proxmox/<int:proxmox_id>/eliminar_clon', methods=['GET'])
@admin_required
@check_proxmox_connection
def eliminar_clon_maquina_virtual(proxmox_id):
    """Elimina una máquina virtual clonada de Proxmox

    Esta ruta se encarga de eliminar una máquina virtual clonada del servidor 
    de Proxmox, eliminando también la conexión de Guacamole si existe y los
    datos almacenados en la base de datos.

    :param proxmox_id: ID de la máquina virtual a eliminar
    :type proxmox_id: int

    :return: Redirige a la página de gestión de máquinas virtuales
    """
    try:
        database_vm = virtual_machines_controller.get_virtual_machine_by_id(proxmox_id)
        if database_vm is None:
            flash(f"La VM {proxmox_id} no se encuentra en la base de datos", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        if database_vm.is_base_vm:
            flash(f"La VM {proxmox_id} es una máquina base y no puede ser eliminada de esta forma", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        proxmox_vm = proxmox.get_vm_by_id(proxmox_id)
        if proxmox_vm is None:
            flash(f"La VM {proxmox_id} no se encuentra en Proxmox", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        if database_vm.guacamole_connection_id:
            try:
                guaca_token = guacamole.get_guacamole_token()
                if guacamole.test_guacamole_connection(guaca_token, database_vm.guacamole_connection_id):
                    guacamole.delete_guacamole_connection(guaca_token, database_vm.guacamole_connection_id)
                else:
                    flash(f"La conexión de Guacamole de la VM {proxmox_id} no existe", "warning")

            except guacamole.GuacamoleError as e:
                # Warning porque es posible que la conexión no existiera en Guacamole
                flash(f"Error al eliminar la conexión de Guacamole: {e}", "warning")

        # Eliminar la máquina virtual de Proxmox
        try:
            proxmox.delete_vm(proxmox_id)
        except (ConnectionError, proxmox.ProxmoxError) as e:
            flash(f"Error al eliminar la VM de Proxmox: {e}", "danger")

        # Eliminar la máquina virtual de la base de datos
        try:
            virtual_machines_controller.delete_virtual_machine(proxmox_id)
        except Exception as e:
            flash(f"Error al eliminar la VM de la base de datos: {e}", "danger")

        sleep(1) # 1 second sleep to give the server time to delete the VM
        flash(f"VM {proxmox_id} eliminada correctamente", "success")


    except Exception as e:
        flash(f"Error al eliminar la VM: {e}", "danger")

    return redirect(url_for('admin_bp.gestion_maquinas'))

@admin_bp.route('/virtual_machines/proxmox/<int:proxmox_id>/test_connection', methods=['GET'])
@admin_required
@check_proxmox_connection
def test_guacamole_connection(proxmox_id):
    """Prueba la conexión de Guacamole de una máquina virtual

    Esta ruta comprueba la conexión de Guacamole de una máquina virtual con el ID dado, creando una conexión si no existe.

    Si la conexión falla, se mostrará un mensaje de error.

    :param proxmox_id: ID de la máquina virtual a probar
    :type proxmox_id: int

    :return: Redirige a la página de detalles de la máquina virtual.
    """

    start_time = time.perf_counter()

    logged_user = session.get('logged_user')
    assert logged_user is not None, "El usuario va a existir por el wrapper"

    try:
        clone_vm = virtual_machines_controller.get_virtual_machine_by_id(proxmox_id)
        if clone_vm is None:
            flash(f"La VM {proxmox_id} no se encuentra en la base de datos", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        base_vm_obj = virtual_machines_controller.get_virtual_machine_by_id(clone_vm.cloned_from)
        if base_vm_obj is None:
            flash(f"La VM base de la VM {proxmox_id} no se encuentra en la base de datos", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        guaca_token = guacamole.get_guacamole_token()
        if not guaca_token:
            raise Exception("No se ha podido obtener el token de Guacamole")

        if clone_vm.guacamole_connection_id:
            # Si la conexión está registrada, se comprueba si existe
            if not guacamole.test_guacamole_connection(guaca_token, clone_vm.guacamole_connection_id):
                virtual_machines_controller.update_virtual_machine(
                    proxmox_id,
                    guacamole_connection_id=None
                )
            else:
                flash(f"Conexión de Guacamole de la VM {proxmox_id} existe", "info")
                return redirect(url_for('admin_bp.editar_maquina_virtual', proxmox_id=base_vm_obj.proxmox_id))

        # Si no existe, se crea una nueva conexión y se prueba
        vm_ip = proxmox.get_vm_ip_addr(clone_vm.proxmox_id)
        guacamole_conn_id = guacamole.create_guacamole_connection(
            token=guaca_token,
            virtual_machine_ip=vm_ip,
            connection_name=f"{clone_vm.nombre}",
            virtual_machine_username=clone_vm.vnc_username,
            connection_password=clone_vm.get_vnc_password()
        )
        if not guacamole_conn_id:
            flash(f"No se ha podido crear la conexión de Guacamole para la VM {proxmox_id}", "danger")
            return redirect(url_for('admin_bp.gestion_maquinas'))

        virtual_machines_controller.update_virtual_machine(
            clone_vm.proxmox_id,
            guacamole_connection_id=guacamole_conn_id
        )

        # Se actualiza la información de la VM clonada
        clone_vm = virtual_machines_controller.get_virtual_machine_by_id(proxmox_id)
        if not clone_vm or not clone_vm.guacamole_connection_id:
            raise Exception("Ha habido un error actualizando la máquina virtual con la conexión de Guacamole")

        if not guacamole.test_guacamole_connection(guaca_token, clone_vm.guacamole_connection_id):
            raise Exception("No se ha podido probar la conexión de Guacamole")

        flash(f"Conexión de Guacamole de la VM {proxmox_id} creada exitosamente", "success")

        elapsed_time = time.perf_counter() - start_time
        logger.info(f"\nTiempo total de Guacamole: {elapsed_time:.3f} segundos\n")

        return redirect(url_for('admin_bp.editar_maquina_virtual', proxmox_id=base_vm_obj.proxmox_id))

    except Exception as e:
        flash(f"Ha sucedido un error innesperado: {e}", "danger")
        return redirect(url_for('admin_bp.gestion_maquinas'))
