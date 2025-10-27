import logging
from app.extensions import db
from app.models import Matricula, Usuario, Asignatura, VirtualMachine
from app.controllers import virtual_machines_controller

from app.utils.enums import EntityType

from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatriculaException(Exception):
    pass

def __check_ids(user_id, asignatura_id):
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

def __remove_user_from_virtual_machine(asignatura_id, user_id):
    """Elimina un usuario de todas las máquinas virtuales de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :param user_id: ID del usuario
    :type user_id: int

    :raises ValueError: si los ID's no son enteros
    :raises SQLAlchemyError: si ocurre un error al eliminar al usuario de las máquinas virtuales
    """
    __check_ids(user_id, asignatura_id)
    try:
        subject_vms = virtual_machines_controller.get_virtual_machine_by_asignatura(asignatura_id)
        student_vms = [vm for vm in subject_vms if vm.user_id == user_id]
        if student_vms:
            for vm in student_vms:
                virtual_machines_controller.update_virtual_machine(
                    vm.proxmox_id,
                    commit=False,
                    user_id=None
                )
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al eliminar al usuario de las máquinas virtuales: {e}") from e

def create_matricula(user_id, asignatura_id):
    """Matricula a un alumno en una asignatura

    :param user_id: ID del alumno
    :type user_id: int

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Objeto matrícula creado
    :rtype: Matricula

    :raises ValueError: si los ID's no son enteros
    :raises MatriculaException: si la matrícula ya existe
    :raises SQLAlchemyError: si ocurre un error al crear la matrícula
    """
    __check_ids(user_id, asignatura_id)

    if Matricula.query.filter_by(
        user_id=user_id,
        asignatura_id=asignatura_id
    ).first():
        raise MatriculaException("La matrícula ya existe")

    try:
        matricula = Matricula(user_id=user_id, asignatura_id=asignatura_id)
        db.session.add(matricula)
        db.session.commit()
        return matricula
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al crear la matrícula: {e}") from e

def create_matriculas_for_entity(entity_type: EntityType, entity_id, lista_ids):
    """
    Crea matrículas para una entidad (asignatura o alumno) dada una lista de ID's

    :param entity_type: Tipo de entidad
    :type entity_type: EntityType

    :param entity_id: ID de la entidad, puede ser el ID de una asignatura o de un alumno
    :type entity_id: int

    :param lista_ids: Lista de ID's a matricular. Si entity_type es asignatura, son ID's de alumnos, si es usuario, son ID's de asignaturas
    :type lista_ids: list

    :return: Lista de matrículas creadas
    :rtype: list[Matricula]

    :raises ValueError: si el tipo de entidad no es válido
    """
    matriculas = []
    if entity_type == EntityType.ASIGNATURA:
        for user_id in lista_ids:
            matricula = Matricula(user_id=user_id, asignatura_id=entity_id)
            db.session.add(matricula)
            matriculas.append(matricula)

    elif entity_type == EntityType.USUARIO:
        for asignatura_id in lista_ids:
            matricula = Matricula(user_id=entity_id, asignatura_id=asignatura_id)
            db.session.add(matricula)
            matriculas.append(matricula)
    else:
        raise ValueError("Tipo de entidad no válido")

    return matriculas

def get_matricula(user_id, asignatura_id):
    """Obtiene la matrícula de un alumno en una asignatura

    :param user_id: ID del alumno
    :type user_id: int

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Matrícula encontrada o None si no se encuentra
    :rtype: Matricula

    :raises ValueError: si los ID's no son enteros
    """
    __check_ids(user_id, asignatura_id)

    return Matricula.query.filter_by(user_id=user_id, asignatura_id=asignatura_id).first()

def get_all_matriculas():
    """Obtiene todas las matrículas registradas en la base de datos

    :return: Lista de matrículas
    :rtype: list[Matricula]
    """
    return Matricula.query.all()

def get_asignaturas_matriculadas(user_id):
    """Obtiene una lista de los ID's de las asignaturas en las que está matriculado un alumno

    :param user_id: ID del alumno
    :type user_id: int

    :return: Lista de ID's de las asignaturas, vacía si no se encuentra
    :rtype: list

    :raises ValueError: si el ID no es un entero
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    return Matricula.query.filter_by(user_id=user_id).all()

def get_alumnos_matriculados(asignatura_id):
    """Obtiene una lista de los alumnos matriculados en una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Lista de matrículas de los alumnos, vacía si no se encuentra
    :rtype: list[Matricula]

    :raises ValueError: si el ID no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    return Matricula.query.filter_by(asignatura_id=asignatura_id).all()

def get_objetos_alumnos_matriculados(asignatura_id):
    """
    Obtiene la lista de usuarios que están matriculados en una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Lista de objetos de los alumnos, vacía si no se encuentra
    :rtype: list[Usuario]

    :raises ValueError: si el ID no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    return Usuario.query.join(Matricula, Usuario.id == Matricula.user_id).filter(Matricula.asignatura_id == asignatura_id).all()

def get_objetos_alumnos_no_matriculados(asignatura_id):
    """
    Obtiene la lista de usuarios que no están matriculados en una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Lista de objetos de los alumnos, vacía si no se encuentra
    :rtype: list[Usuario]

    :raises ValueError: si el ID no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    return Usuario.query.filter(~Usuario.matriculas.any(Matricula.asignatura_id == asignatura_id)).all()

def get_objetos_asignaturas_matriculadas(user_id):
    """
    Obtiene la lista de asignaturas a las que está matriculado un alumno

    :param user_id: ID del alumno
    :type user_id: int

    :return: Lista de objetos de las asignaturas, vacía si no se encuentra
    :rtype: list[Asignatura]

    :raises ValueError: si el ID no es un entero
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    return Asignatura.query.join(Matricula, Asignatura.id == Matricula.asignatura_id).filter(Matricula.user_id == user_id).all()

def get_objectos_asignaturas_no_matriculadas(user_id):
    """
    Obtiene la lista de asignaturas en las que no está matriculado un alumno

    :param user_id: ID del alumno
    :type user_id: int

    :return: Lista de objetos de las asignaturas, vacía si no se encuentra
    :rtype: list[Asignatura]

    :raises ValueError: si el ID no es un entero
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    return Asignatura.query.filter(~Asignatura.matriculas.any(Matricula.user_id == user_id)).all()

def update_matriculas_for_entity(entity_type: EntityType, entity_id, lista_ids):
    """
    Actualiza las matrículas de una entidad (asignatura o alumno) dada una lista de ID's

    NOTA: No se realiza commit en esta función, por lo que el llamante debe hacerlo

    :param entity_type: Tipo de entidad
    :type entity_type: EntityType

    :param entity_id: ID de la entidad, puede ser el ID de una asignatura o de un alumno
    :type entity_id: int

    :param lista_ids: Lista de ID's a matricular. Si entity_type es asignatura, son ID's de alumnos, si es usuario, son ID's de asignaturas
    :type lista_ids: set

    :return: Lista de matrículas creadas
    :rtype: list[Matricula]

    :raises ValueError: si el tipo de entidad no es válido
    :raises SQLAlchemyError: si ocurre un error al actualizar las matrículas
    :raises MatriculaException: si ocurre un error inesperado
    """
    if not isinstance(entity_id, int):
        raise ValueError("El ID de la entidad debe ser un entero")

    entity_ids_actuales = set()
    try:
        # Separar por tipo de entidad
        if entity_type == EntityType.ASIGNATURA:
            matriculas_actuales = get_alumnos_matriculados(entity_id)
            entity_ids_actuales = {matricula.user_id for matricula in matriculas_actuales}

        elif entity_type == EntityType.USUARIO:
            matriculas_actuales = get_asignaturas_matriculadas(entity_id)
            entity_ids_actuales = {matricula.asignatura_id for matricula in matriculas_actuales}

        else:
            raise ValueError("Tipo de entidad no válido")

        # Matrículas a añadir y a eliminar
        to_add_enrollments = lista_ids - entity_ids_actuales
        to_remove_enrollments = entity_ids_actuales - lista_ids

        # Eliminar matrículas
        if to_remove_enrollments:
            if entity_type == EntityType.ASIGNATURA:
                Matricula.query.filter(
                    Matricula.asignatura_id == entity_id,
                    Matricula.user_id.in_(to_remove_enrollments)
                ).delete(synchronize_session='fetch')

                for user_id in to_remove_enrollments:
                    __remove_user_from_virtual_machine(entity_id, user_id)

            elif entity_type == EntityType.USUARIO:
                Matricula.query.filter(
                    Matricula.user_id == entity_id,
                    Matricula.asignatura_id.in_(to_remove_enrollments)
                ).delete(synchronize_session='fetch')

                for asignatura_id in to_remove_enrollments:
                    __remove_user_from_virtual_machine(asignatura_id, entity_id)
        
        # Añadir matrículas
        matriculas = []
        if entity_type == EntityType.ASIGNATURA:
            for user_id in to_add_enrollments:
                matricula = Matricula(user_id=user_id, asignatura_id=entity_id)
                matriculas.append(matricula)
                db.session.add(matricula)
        
        elif entity_type == EntityType.USUARIO:
            for asignatura_id in to_add_enrollments:
                matricula = Matricula(user_id=entity_id, asignatura_id=asignatura_id)
                matriculas.append(matricula)
                db.session.add(matricula)

        return matriculas

    except SQLAlchemyError as e:
        logger.error(f"Error updating matriculas for entity {entity_type} with ID {entity_id}: {e}")
        raise SQLAlchemyError(f"Error al actualizar las matrículas: {e}") from e

    except Exception as e:
        logger.error(f"Error updating matriculas for entity {entity_type} with ID {entity_id}: {e}")
        raise MatriculaException(f"Ha ocurrido un error inesperado: {e}") from e

def delete_matricula(user_id, asignatura_id):
    """Borra la matrícula de un alumno en una asignatura

    :param user_id: ID del alumno
    :type user_id: int

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Matrícula eliminada
    :rtype: Matricula

    :raises ValueError: si los ID's no son enteros
    :raises MatriculaException: si la matrícula no existe
    :raises SQLAlchemyError: si ocurre un error al borrar la matrícula
    """
    __check_ids(user_id, asignatura_id)
    try:
        matricula = get_matricula(user_id, asignatura_id)
        if not matricula:
            raise MatriculaException("Matrícula no encontrada")

        # Eliminar al usuario de las máqinas virtuales que tenga asignadas
        __remove_user_from_virtual_machine(asignatura_id, user_id)
        
        db.session.delete(matricula)
        db.session.commit()

        return matricula
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al borrar la matrícula: {e}") from e
