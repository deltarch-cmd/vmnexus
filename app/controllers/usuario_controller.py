import logging
from app.extensions import db
from app.models.usuario import Usuario
from app.controllers.matricula_controller import create_matriculas_for_entity, update_matriculas_for_entity 

from app.utils.enums import EntityType

from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UsuarioException(Exception):
    pass

def create_user(nombre, email, password, is_admin=False):
    """Crea un nuevo usuario en la base de datos

    :param nombre: Nombre del usuario
    :type nombre: str

    :param email: Correo electrónico del usuario
    :type email: str

    :param password: Contraseña del usuario
    :type password: str

    :param is_admin: Indica si el usuario es administrador (default: False)
    :type is_admin: bool

    :return: Usuario creado
    :rtype: Usuario

    :raises UsuarioException: Si el correo electrónico ya está en uso o hay un error al guardar la contraseña
    :raises SQLAlchemyError: Si ocurre un error al guardar el usuario
    """
    if Usuario.query.filter_by(email=email).first():
        raise UsuarioException(f"El correo electrónico '{email}' ya está en uso")

    try:
        user = Usuario(
            nombre=nombre,
            email=email,
            nombre_usuario=email.split('@')[0],
            password_hash='',
            is_admin=is_admin
        )

        user.set_password(password)
        if not user.check_password(password): # Verifica que la contraseña se haya guardado correctamente
            raise UsuarioException("Error al guardar la contraseña, inténtelo de nuevo")

        db.session.add(user)
        db.session.commit()
        return user

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al guardar el usuario: {e}") from e

def create_user_with_matriculas(nombre, email, password, lista_id_asignaturas, is_admin=False):
    """Crea un nuevo usuario en la base de datos con sus matrículas asociadas

    :param nombre: Nombre del usuario
    :type nombre: str

    :param email: Correo electrónico del usuario
    :type email: str

    :param password: Contraseña del usuario
    :type password: str

    :param lista_id_asignaturas: Lista de IDs de las asignaturas a matricular
    :type lista_id_asignaturas: list[int]

    :param is_admin: Indica si el usuario es administrador (default: False)
    :type is_admin: bool

    :return: Usuario creado
    :rtype: Usuario

    :raises UsuarioException: Si el correo electrónico ya está en uso o hay un error al guardar la contraseña
    :raises ValueError: Si hay un error al crear las matrículas
    :raises SQLAlchemyError: Si ocurre un error al guardar el usuario
    """
    try:
        with db.session.begin_nested():
            new_user = Usuario(
                nombre=nombre,
                email=email,
                nombre_usuario=email.split('@')[0],
                password_hash='',
                is_admin=is_admin
            )

            if Usuario.query.filter_by(email=email).first():
                raise UsuarioException(f"El correo electrónico '{email}' ya está en uso")

            new_user.set_password(password)
            if not new_user.check_password(password):
                raise UsuarioException('Error al guardar la contraseña, inténtelo de nuevo')

            db.session.add(new_user)
            db.session.flush() # Se hace flush para obtener el ID del usuario

            create_matriculas_for_entity(EntityType.USUARIO, new_user.id, lista_id_asignaturas)
        
        db.session.commit() # Se confirman los cambios

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al crear el usuario con matrículas: {e}") from e

    return new_user

# UNUSED: Esta función puede ser usada como base si se implementa el bulk_add en la página de usuarios
## Debido a falta de tiempo, esta funcionalidad no fue implementada
def bulk_create_usuarios(lista_usuarios):
    """Crea varios usuarios en la base de datos

    :param lista_usuarios: Lista de usuarios a crear. Cada usuario es un diccionario con los siguientes campos:
        - nombre: Nombre del usuario
        - email: Correo electrónico del usuario
        - password: Contraseña del usuario
        - rol: Rol del usuario (default: "alumno")
    :type lista_usuarios: list[dict]

    :return: Lista de usuarios creados
    :rtype: list[dict]

    :raises UsuarioException: Si el correo electrónico ya está en uso o hay un error al guardar la contraseña
    :raises SQLAlchemyError: Si hay un error al crear los usuarios
    """
    try:
        for user_data in lista_usuarios:
            nombre = user_data.get('nombre')
            email = user_data.get('email')
            password = user_data.get('password')
            is_admin = user_data.get('rol', "alumno") == "admin"

            user = Usuario(
                nombre=nombre,
                email=email,
                nombre_usuario=email.split('@')[0],
                password_hash='',
                is_admin=is_admin
            )

            if Usuario.query.filter_by(email=email).first():
                raise UsuarioException(f"El correo electrónico '{email}' ya está en uso")

            user.set_password(password)
            if not user.check_password(password):
                raise UsuarioException('Error al guardar la contraseña, inténtelo de nuevo')

            db.session.add(user)

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al crear los usuarios: {e}") from e

    return lista_usuarios

def get_usuario_by_id(user_id):
    """Obtiene un usuario por su ID

    :param user_id: ID del usuario
    :type user_id: int

    :return: Usuario encontrado o None si no se encuentra
    :rtype: Usuario

    :raises ValueError: Si user_id no es un entero
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    return Usuario.query.get(user_id) # Retorna None si no se encuentra el usuario

def get_usuario_by_nombre_usuario(nombre_usuario):
    """Obtiene un usuario por su nombre de usuario

    :param nombre_usuario: Nombre de usuario
    :type nombre_usuario: str

    :return: Usuario encontrado o None si no se encuentra
    :rtype: Usuario
    """
    return Usuario.query.filter_by(nombre_usuario=nombre_usuario).first() # Retorna None si no se encuentra el usuario

def get_usuario_by_email(email):
    """Obtiene un usuario por su correo electrónico

    :param email: Correo electrónico del usuario
    :type email: str

    :return: Usuario encontrado o None si no se encuentra
    :rtype: Usuario
    """
    return Usuario.query.filter_by(email=email).first() # Retorna None si no se encuentra el usuario

def get_all_usuarios():
    """Obtiene todos los usuarios registrados

    :return: Lista de usuarios
    :rtype: list[Usuario]
    """
    return Usuario.query.all()

def authenticate_user(email, password):
    """Autentica a un usuario en el sistema

    :param email: Correo electrónico del usuario
    :type email: str

    :param password: Contraseña del usuario
    :type password: str

    :return: Usuario autenticado
    :rtype: Usuario

    :raises UsuarioException: Si el usuario no se encuentra o la contraseña es incorrecta
    """
    user = get_usuario_by_email(email)
    if not user:
        raise UsuarioException("Usuario no encontrado")

    if not user.check_password(password):
        raise UsuarioException("Contraseña incorrecta")

    return user

def update_user_password(user_id, old_password, new_password):
    """Actualiza la contraseña de un usuario

    :param user_id: ID del usuario
    :type user_id: int

    :param old_password: Contraseña actual del usuario
    :type old_password: str

    :param new_password: Nueva contraseña del usuario
    :type new_password: str

    :return: Usuario actualizado o None si no se encuentra
    :rtype: Usuario

    :raises UsuarioException: Si la contraseña actual no coincide
    :raises ValueError: Si user_id no es un entero
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    try:
        user = Usuario.query.get(user_id)
        if not user:
            raise UsuarioException("Usuario no encontrado")

        if not user.check_password(old_password):
            raise UsuarioException("La contraseña actual no coincide")

        user.set_password(new_password)
        user.first_login = False
        db.session.commit()
        return user

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al actualizar la contraseña del usuario: {e}") from e

def update_usuario(user_id, nombre, email, is_admin=False):
    """Actualiza los datos de un usuario

    :param user_id: ID del usuario
    :type user_id: int

    :param nombre: Nombre del usuario
    :type nombre: str

    :param email: Correo electrónico del usuario
    :type email: str

    :param is_admin: Indica si el usuario es administrador (default: False)
    :type is_admin: bool

    :return: Usuario actualizado
    :rtype: Usuario
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    try:
        user = Usuario.query.get(user_id)
        if not user:
            raise UsuarioException("Usuario no encontrado")

        user.nombre = nombre
        user.email = email
        user.is_admin = is_admin
        db.session.commit()
        return user

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al actualizar el usuario: {e}") from e

def update_usuario_with_matriculas(user_id, nombre, email, lista_id_asignaturas, is_admin=False):
    """Actualiza los datos de un usuario y sus matrículas asociadas

    :param user_id: ID del usuario
    :type user_id: int

    :param nombre: Nombre del usuario
    :type nombre: str

    :param email: Correo electrónico del usuario
    :type email: str

    :param lista_id_asignaturas: Lista de IDs de las asignaturas a matricular
    :type lista_id_asignaturas: list[int]

    :param is_admin: Indica si el usuario es administrador (default: False)
    :type is_admin: bool

    :return: Usuario actualizado
    :rtype: Usuario

    :raises UsuarioException: Si el usuario no se encuentra
    :raises ValueError: Si user_id no es un entero o hay un error al actualizar las matrículas
    :raises SQLAlchemyError: Si ocurre un error al actualizar el usuario
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    try:
        user = get_usuario_by_id(user_id)
        if not user:
            raise UsuarioException("Usuario no encontrado")

        with db.session.begin_nested():
            user.nombre = nombre
            user.email = email
            user.is_admin = is_admin

            update_matriculas_for_entity(EntityType.USUARIO, user_id, lista_id_asignaturas)
        
        db.session.commit() # Se confirman los cambios
        return user

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al actualizar el usuario con matrículas: {e}") from e
    
def delete_usuario(user_id):
    """Elimina un usuario de la base de datos

    :param user_id: ID del usuario
    :type user_id: int

    :return: Usuario eliminado
    :rtype: Usuario

    :raises ValueError: Si user_id no es un entero
    :raises UsuarioException: Si el usuario no se encuentra
    :raises SQLAlchemyError: Si ocurre un error al eliminar el usuario
    """
    if not isinstance(user_id, int):
        raise ValueError("El ID del usuario debe ser un entero")

    try:
        user = Usuario.query.get(user_id)
        if not user:
            raise UsuarioException("Usuario no encontrado")

        db.session.delete(user)
        db.session.commit()
        return user

    except SQLAlchemyError as e:
        db.session.rollback()
        raise SQLAlchemyError(f"Error al eliminar el usuario: {e}") from e
