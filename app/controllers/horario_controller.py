from app.extensions import db
from app.models import Horario

from sqlalchemy.exc import SQLAlchemyError

class HorarioException(Exception):
    pass

def create_horario(dia, hora_inicio, hora_fin, asignatura_id):
    """Crea un nuevo horario en la base de datos

    :param dia: Día de la semana del objecto
    :type dia: str

    :param hora_inicio: Hora de inicio del objecto
    :type hora_inicio: str

    :param hora_fin: Hora de fin del objecto
    :type hora_fin: str

    :param asignatura_id: ID de la asignatura a la que pertenece el horario
    :type asignatura_id: int

    :return: Horario creado
    :rtype: Horario

    :raises ValueError: Si asignatura_id no es un entero
    :raises SQLAlchemyError: Si ocurre un error al crear el horario
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    try:
        horario = Horario(dia, hora_inicio, hora_fin, asignatura_id)
        db.session.add(horario)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al crear el horario: {e}") from e

    return horario

def bulk_create_horarios(horarios, asignatura_id):
    """Crea varios horarios en la base de datos

    NOTA: El commit se hace en la función llamante

    :param horarios: Lista de horarios a crear. Cada horario es un diccionario con los siguientes campos:
        - id: ID del horario (opcional, debe ser '')
        - dia: Día de la semana
        - hora_inicio: Hora de inicio
        - hora_fin: Hora de fin
    :type horarios: list

    :param asignatura_id: ID de la asignatura a la que pertenecen los horarios
    :type asignatura_id: int

    :raises ValueError: Si asignatura_id no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    with db.session.begin_nested():
        for horario in horarios:
            horario_obj = Horario(
                horario['dia'],
                horario['hora_inicio'],
                horario['hora_fin'],
                asignatura_id
            )
            db.session.add(horario_obj)

def get_all_horarios_by_asignatura(asignatura_id):
    """Obtiene todos los horarios de una asignatura

    :param asignatura_id: ID de la asignatura
    :type asignatura_id: int

    :return: Lista de horarios
    :rtype: list[Horario]

    :raises ValueError: Si asignatura_id no es un entero
    """
    if not isinstance(asignatura_id, int):
        raise ValueError("El ID de la asignatura debe ser un entero")

    return Horario.query.filter_by(asignatura_id=asignatura_id).all()

def update_horario(horario_id, asignatura_id, **kwargs):
    """Actualiza un horario en la base de datos

    :param horario_id: ID del horario a actualizar
    :type horario_id: int

    :param asignatura_id: ID de la asignatura a la que pertenece
    :type asignatura_id: int

    :param kwargs: Datos a actualizar
    :type kwargs: dict

    :return: Horario actualizado
    :rtype: Horario

    :raises ValueError: Si horario_id no es un entero
    :raises SQLAlchemyError: Si ocurre un error al actualizar el horario
    """
    if not isinstance(horario_id, int):
        raise ValueError("El ID del horario debe ser un entero")

    try:
        horario = Horario.query.get(horario_id)
        if not horario:
            raise HorarioException("Horario no encontrado")

        if horario.asignatura_id != asignatura_id:
            raise HorarioException("El horario no pertenece a la asignatura")

        for key, value in kwargs.items():
            setattr(horario, key, value)

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al actualizar el horario: {e}") from e

    return horario

def bulk_update_horarios(horarios_data, asignatura_id):
    """Actualiza varios horarios en la base de datos

    NOTA: El commit se hace en la función llamante

    :param horarios_data: Lista de horarios a actualizar. Cada horario es un diccionario con los siguientes campos:
        - id: ID del horario
        - dia: Día de la semana
        - hora_inicio: Hora de inicio
        - hora_fin: Hora de fin
    :type horarios_data: list

    :param asignatura_id: ID de la asignatura a la que pertenecen los horarios
    :type asignatura_id: int

    :raises ValueError: Si asignatura_id no es un entero
    """
    existing_horarios = {
        horario.id: horario for horario in get_all_horarios_by_asignatura(asignatura_id)
    }
    updated_horarios_ids = set()

    with db.session.begin_nested():
        for horario in horarios_data:
            horario_id = horario.get('id')
            dia = horario['dia']
            hora_inicio = horario['hora_inicio']
            hora_fin = horario['hora_fin']

            if horario_id in existing_horarios:
                existing_horario = existing_horarios[horario_id]
                existing_horario.dia = dia
                existing_horario.hora_inicio = hora_inicio
                existing_horario.hora_fin = hora_fin

                updated_horarios_ids.add(horario_id)
            else:
                new_horario = Horario(dia, hora_inicio, hora_fin, asignatura_id)
                db.session.add(new_horario)

        # Eliminar los horarios que no se actualizaron
        for horario_id, horario in existing_horarios.items():
            if horario_id not in updated_horarios_ids:
                db.session.delete(horario)

def delete_horario(horario_id):
    """Elimina un horario de la base de datos

    :param horario_id: ID del horario a eliminar
    :type horario_id: int

    :return: Horario eliminado
    :rtype: Horario

    :raises ValueError: Si horario_id no es un entero
    :raises SQLAlchemyError: Si ocurre un error al eliminar el horario
    """
    if not isinstance(horario_id, int):
        raise ValueError("El ID del horario debe ser un entero")

    try:
        horario = Horario.query.get(horario_id)
        if not horario:
            raise HorarioException("Horario no encontrado")

        db.session.delete(horario)
        db.session.commit()
        return horario

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al eliminar el horario: {e} ") from e
