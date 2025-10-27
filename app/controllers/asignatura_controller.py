from app.extensions import db
from app.models import Asignatura, VirtualMachine

from app.controllers.laboratorio_controller import bulk_create_laboratorios, bulk_update_laboratorios
from app.controllers.matricula_controller import create_matriculas_for_entity, update_matriculas_for_entity
from app.controllers.horario_controller import bulk_create_horarios, bulk_update_horarios

from app.utils.enums import EntityType

from sqlalchemy.exc import SQLAlchemyError

class AsignaturaException(Exception):
    pass

def create_asignatura(nombre, profesor_id, descripcion=None):
    """Crea una nueva asignatura en la base de datos

    :param nombre: Nombre de la asignatura
    :type nombre: str

    :param profesor_id: ID del usuario que imparte la asignatura
    :type profesor_id: int

    :param descripcion: Descripción de la asignatura (default: None)
    :type descripcion: str

    :return: Asignatura creada
    :rtype: Asignatura

    :raises AsignaturaException: Si ya existe una asignatura con el mismo nombre
    :raises SQLAlchemyError: Si ocurre un error al crear la asignatura
    """
    if Asignatura.query.filter_by(nombre=nombre).first():
        raise AsignaturaException(f"Ya existe una asignatura con el nombre '{nombre}'")

    try:
        asignatura = Asignatura(nombre, profesor_id, descripcion)
        db.session.add(asignatura)
        db.session.commit()
        return asignatura
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al crear la asignatura: {e}") from e

def create_asignatura_with_entidades(nombre, profesor_id, descripcion=None, labs_data=None, lista_id_alumnos=None, horarios_data=None):
    """
    Crea una nueva asignatura en la base de datos con sus entidades asociadas

    Las entidades asociadas son laboratorios, matrículas y horarios

    :param nombre: Nombre de la asignatura
    :type nombre: str

    :param profesor_id: ID del profesor que imparte la asignatura
    :type profesor_id: int

    :param descripcion: Descripción de la asignatura (default: None)
    :type descripcion: str

    :param labs_data: Datos de los laboratorios a crear (default: None)
    :type labs_data: list[dict]

    :param lista_id_alumnos: Lista de IDs de alumnos a matricular (default: None)
    :type lista_id_alumnos: list[int]

    :param horarios_data: Datos de los horarios a crear (default: None)
    :type horarios_data: list[dict]

    :return: Asignatura creada
    :rtype: Asignatura

    :raises AsignaturaException: Si ocurre un error al crear la asignatura
    """
    try:
        with db.session.begin_nested():
            new_asignatura = Asignatura(nombre, profesor_id, descripcion)
            db.session.add(new_asignatura)
            db.session.flush() # Se hace flush para obtener el ID de la asignatura

            if labs_data:
                bulk_create_laboratorios(labs_data, new_asignatura.id, profesor_id)

            if lista_id_alumnos:
                create_matriculas_for_entity(EntityType.ASIGNATURA, new_asignatura.id, lista_id_alumnos)

            if horarios_data:
                bulk_create_horarios(horarios_data, new_asignatura.id)
        
        db.session.commit()
    
    except (SQLAlchemyError, Exception) as e:
        db.session.rollback()
        raise AsignaturaException(f"Error al crear la asignatura con entidades: {e}")
    
    return new_asignatura

def get_asignatura_by_id(asignatura_id):
    """Obtiene una asignatura por su ID

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Asignatura encontrada o None si no se encuentra
    :rtype: Asignatura

    :raises ValueError: Si asignatura_id no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("asignatura_id debe ser un entero")

    return Asignatura.query.get(asignatura_id)

def get_all_asignaturas():
    """Obtiene todas las asignaturas registradas en la base de datos
    
    :return: Lista de asignaturas
    :rtype: list[Asignatura]
    """
    return Asignatura.query.all()

# Probar a usar esto en vez del "with_labs" en donde sea que se use
def get_asignatura_by_profesor(profesor_id):
    """Obtiene todas las asignaturas de un profesor

    :param profesor_id: ID del profesor
    :type profesor_id: int

    :return: Lista de asignaturas del profesor
    :rtype: list[Asignatura]

    :raises ValueError: Si profesor_id no es un entero
    """
    if not isinstance(profesor_id, int):
        raise ValueError("profesor_id debe ser un entero")

    return Asignatura.query.filter_by(profesor_id=profesor_id).all()

def get_asignaturas_without_virtual_machines():
    """Obtiene todas las asignaturas que no tienen máquinas virtuales asociadas

    :return: Lista de asignaturas sin máquinas virtuales
    :rtype: list[Asignatura]
    """
    return (
        Asignatura.query
        .outerjoin(VirtualMachine)
        .filter(VirtualMachine.proxmox_id == None)
        .all()
    )

def update_asignatura(asignatura_id, nombre, descripcion=None, labs_data=None, lista_id_alumnos=None, horarios_data=None):
    """Actualiza los datos de una asignatura y sus entidades asociadas

    Las entidades asociadas son laboratorios, matrículas y horarios

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :param nombre: Nuevo nombre de la asignatura
    :type nombre: str

    :param descripcion: Nueva descripción de la asignatura (default: None)
    :type descripcion: str

    :param labs_data: Datos de los laboratorios a actualizar (default: None)
    :type labs_data: list[dict]

    :param lista_id_alumnos: Lista de IDs de alumnos a matricular (default: None)
    :type lista_id_alumnos: list[int]

    :param horarios_data: Datos de los horarios a actualizar (default: None)
    :type horarios_data: list[dict]

    :return: Asignatura actualizada
    :rtype: Asignatura

    :raises ValueError: Si asignatura_id no es un entero
    :raises AsignaturaException: Si no se encuentra la asignatura u ocurre un error al actualizar la asignatura
    :raises Exception: Si ocurre un error inesperado
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("asignatura_id debe ser un entero")

    asignatura = get_asignatura_by_id(asignatura_id)
    if not asignatura:
        raise AsignaturaException(f"Asignatura con id {asignatura_id} no encontrada")

    try:
        with db.session.begin_nested():
            asignatura.nombre = nombre
            asignatura.descripcion = descripcion

            if labs_data:
                bulk_update_laboratorios(labs_data, asignatura_id, asignatura.profesor_id)

            if lista_id_alumnos:
                update_matriculas_for_entity(EntityType.ASIGNATURA, asignatura_id, lista_id_alumnos)

            if horarios_data:
                bulk_update_horarios(horarios_data, asignatura_id)

        db.session.commit()

    except SQLAlchemyError as e:
        db.session.rollback()
        raise AsignaturaException(f"Error al actualizar la asignatura: {e}")

    except Exception as e:
        db.session.rollback()
        raise AsignaturaException(f"Ha ocurrido un error inesperado: {e}")

    return asignatura

def delete_asignatura(asignatura_id):
    """Elimina una asignatura por su ID

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: True si se elimina, False si no se encuentra
    :rtype: bool

    :raises ValueError: Si asignatura_id no es un entero
    :raises AsignaturaException: Si no se encuentra la asignatura o ocurre un error al eliminarla
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("asignatura_id debe ser un entero")

    try:
        asignatura = Asignatura.query.get(asignatura_id)
        if not asignatura:
            raise AsignaturaException(f"Asignatura con id {asignatura_id} no encontrada")

        db.session.delete(asignatura)
        db.session.commit()
        return asignatura
    except SQLAlchemyError as e:
        db.session.rollback()
        raise AsignaturaException(f"Error al eliminar la asignatura: {e}")
