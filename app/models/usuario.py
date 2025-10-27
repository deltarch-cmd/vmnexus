from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    """Modelo de la tabla usuarios en la base de datos

    Atributos:
        id (int): ID del usuario
        nombre (str): Nombre completo del usuario
        email (str): Correo electrónico del usuario
        nombre_usuario (str): Nombre de usuario, es el correo sin el dominio
        password_hash (str): Contraseña del usuario
        is_admin (bool): Indica si el usuario es administrador
        created_at (datetime): Fecha de creación del usuario
        first_login (bool): Indica si es la primera vez que el usuario inicia sesión

        matriculas (list[Matricula]): Lista de matrículas asociadas al usuario
        virtual_machines (list[VirtualMachine]): Lista de máquinas virtuales asociadas al usuario
    """
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    nombre_usuario = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    first_login = db.Column(db.Boolean, default=True)

    matriculas = db.relationship('Matricula', back_populates='usuario', cascade='all, delete-orphan', passive_deletes=True)
    virtual_machines = db.relationship('VirtualMachine', back_populates='usuario', lazy='dynamic')

    def set_password(self, password):
        """Genera el hash de la contraseña del usuario y la asigna al objeto

        :param password: Contraseña del usuario
        :type password: str
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña ingresada es correcta

        :param password: Contraseña a verificar
        :type password: str

        :return: True si la contraseña es correcta, False en caso contrario
        :rtype: bool
        """
        return check_password_hash(self.password_hash, password)

    def __init__(self, nombre, email, nombre_usuario, password_hash, is_admin=False):
        """Constructor del modelo usuarios
        
        :param nombre: Nombre completo del usuario
        :type nombre: str

        :param email: Correo electrónico del usuario
        :type email: str

        :param nombre_usuario: Nombre de usuario, es el correo sin el dominio
        :type nombre_usuario: str

        :param password_hash: Contraseña del usuario (hash)
        :type password_hash: str

        :param is_admin: Indica si el usuario es administrador (default: False)
        :type is_admin: bool
        """
        self.nombre = nombre
        self.email = email
        self.nombre_usuario = nombre_usuario
        self.password_hash = password_hash
        self.is_admin = is_admin

    def serialize(self):
        """Serializa el objeto usuario a un diccionario

        :return: Diccionario con los datos del usuario
        :rtype: dict
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'nombre_usuario': self.nombre_usuario,
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }

    def __repr__(self):
        """Representación del usuario como string
        
        :return: Representación del usuario
        :rtype: str
        """
        return f"Usuario({self.nombre}, {self.email})"
