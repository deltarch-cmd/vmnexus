from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.laboratorio import Laboratorio

class LaboratorioException(Exception):
    pass

def __check_ids(asignatura_id, profesor_id):
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    if not isinstance(profesor_id, int):
        raise ValueError("El ID del profesor debe ser un entero")

def create_laboratorio(nombre, asignatura_id, profesor_id):
    """Crea un nuevo laboratorio en la base de datos

    :param nombre: Nombre del laboratorio
    :type nombre: str

    :param asignatura_id: ID de la asignatura a la que pertenece el laboratorio
    :type asignatura_id: int

    :param profesor_id: ID del profesor que crea el laboratorio
    :type profesor_id: int

    :return: Laboratorio creado
    :rtype: Laboratorio

    :raises LaboratorioException: Si hay un error al crear el laboratorio o con los datos proporcionados
    """
    __check_ids(asignatura_id, profesor_id)

    if Laboratorio.query.filter_by(nombre=nombre, asignatura_id=asignatura_id).first():
        raise LaboratorioException("Ya existe un laboratorio con ese nombre en la asignatura")

    try:
        laboratorio = Laboratorio(nombre, asignatura_id, profesor_id)
        db.session.add(laboratorio)
        db.session.commit()
        return laboratorio

    except SQLAlchemyError as e:
        db.session.rollback()
        raise LaboratorioException(f"Error al crear el laboratorio: {e}") from e

def bulk_create_laboratorios(labs_data, asignatura_id, profesor_id):
    """Crea varios laboratorios en la base de datos

    NOTA: El commit se hace en la función llamante

    :param labs_data: Lista de laboratorios a crear. Cada laboratorio es un diccionario con los siguientes campos:
        - nombre: Nombre del laboratorio
        - pdf_url: URL del archivo PDF del laboratorio (opcional)
    :type labs_data: list

    :param asignatura_id: ID de la asignatura a la que pertenecen los laboratorios
    :type asignatura_id: int

    :param profesor_id: ID del profesor que crea los laboratorios
    :type profesor_id: int

    :return: Lista de laboratorios creados
    :rtype: list[Laboratorio]

    :raises ValueError: Si asignatura_id o profesor_id no son enteros
    """
    __check_ids(asignatura_id, profesor_id)

    with db.session.begin_nested():
        laboratorios = []
        for data in labs_data:
            laboratorio = Laboratorio(
                data['nombre'],
                asignatura_id,
                profesor_id,
                data.get('pdf_url', None)
            )
            db.session.add(laboratorio)
            laboratorios.append(laboratorio)

    return laboratorios

def get_laboratorio_by_id(laboratorio_id):
    """Obtiene un laboratorio por su ID

    :param laboratorio_id: ID del laboratorio
    :type laboratorio_id: int

    :return: Laboratorio encontrado o None si no se encuentra
    :rtype: Laboratorio
    """
    return Laboratorio.query.get(laboratorio_id)

def get_all_laboratorios():
    """Obtiene todos los laboratorios registrados

    :return: Lista de laboratorios
    :rtype: list[Laboratorio]
    """
    return Laboratorio.query.all()

def get_laboratorios_by_asignatura(asignatura_id):
    """Obtiene todos los laboratorios de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Lista de laboratorios
    :rtype: list[Laboratorio]

    :raises ValueError: Si asignatura_id no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    return Laboratorio.query.filter_by(asignatura_id=asignatura_id).all()

def bulk_update_laboratorios(labs_data, asignatura_id, profesor_id):
    """Actualiza los laboratorios de una asignatura

    NOTA: El commit se hace en la función llamante

    :param labs_data: Lista de laboratorios a actualizar. Cada laboratorio es un diccionario con los siguientes campos:
        - id: ID del laboratorio (opcional, debe ser '')
        - nombre: Nombre del laboratorio
        - pdf_url: URL del archivo PDF del laboratorio (opcional)
    :type labs_data: list

    :param asignatura_id: ID de la asignatura a la que pertenecen los laboratorios
    :type asignatura_id: int

    :param profesor_id: ID del profesor que actualiza los laboratorios
    :type profesor_id: int

    :raises ValueError: Si asignatura_id o profesor_id no son enteros
    """
    __check_ids(asignatura_id, profesor_id)

    existing_labs = {
        lab.id: lab for lab in get_laboratorios_by_asignatura(asignatura_id)
    }
    updated_lab_ids = set() # Set para guardar los IDs de los laboratorios actualizados

    with db.session.begin_nested():
        for data in labs_data:
            lab_id = data.get('id')
            lab_name = data['nombre']
            lab_pdf_url = data.get('pdf_url', None)

            if lab_id in existing_labs:
                existing_lab = existing_labs[lab_id]
                existing_lab.nombre = lab_name
                if lab_pdf_url:
                    existing_lab.pdf_url = lab_pdf_url

                updated_lab_ids.add(lab_id)
            else:
                new_lab = Laboratorio(lab_name, asignatura_id, profesor_id, lab_pdf_url)
                db.session.add(new_lab)

        # Eliminar los laboratorios que no se actualizaron
        for lab_id, lab in existing_labs.items():
            if lab_id not in updated_lab_ids:
                db.session.delete(lab)

def delete_laboratorio(laboratorio_id):
    """Elimina un laboratorio por su ID

    :param laboratorio_id: ID del laboratorio a eliminar
    :type laboratorio_id: int

    :return: Laboratorio eliminado
    :rtype: Laboratorio

    :raises ValueError: Si laboratorio_id no es un entero
    :raises LaboratorioException: Si ocurre un error al eliminar el laboratorio
    """
    if not isinstance(laboratorio_id, int):
        raise ValueError("El ID del laboratorio debe ser un entero")

    try:
        laboratorio = get_laboratorio_by_id(laboratorio_id)
        if not laboratorio:
            raise LaboratorioException("Laboratorio no encontrado")

        db.session.delete(laboratorio)
        db.session.commit()
        return laboratorio
    except SQLAlchemyError as e:
        db.session.rollback()
        raise LaboratorioException(f"Error al eliminar el laboratorio: {e}") from e

def delete_all_laboratorios_by_asignatura(asignatura_id):
    """Elimina todos los laboratorios de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Laboratorios eliminados
    :rtype: list[Laboratorio]

    :raises ValueError: Si asignatura_id no es un entero
    :raises LaboratorioException: Si ocurre un error al eliminar los laboratorios
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    try:
        laboratorios = get_laboratorios_by_asignatura(asignatura_id)
        if not laboratorios:
            raise LaboratorioException("No se encontraron laboratorios para la asignatura")

        db.session.delete(laboratorios) # Se eliminan todos los laboratorios de la asignatura
        db.session.commit()
        return laboratorios

    except SQLAlchemyError as e:
        db.session.rollback()
        raise LaboratorioException(f"Error al eliminar los laboratorios: {e}") from e
