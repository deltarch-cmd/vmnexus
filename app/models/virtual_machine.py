from cryptography.fernet import Fernet
from app.extensions import db

from app.models.asignatura import Asignatura
from app.models.usuario import Usuario

from app.config import FlaskAppConfig
key = FlaskAppConfig.ENCRYPTION_KEY # Clave de cifrado para las contraseñas VNC

class VirtualMachine(db.Model):
    """Modelo de la tabla virtual_machines en la base de datos

    Atributos:
        proxmox_id (int): ID de la máquina virtual en Proxmox
        guacamole_connection_id (int): ID de la conexión en Guacamole
        user_id (int): ID del usuario propietario de la máquina virtual
        asignatura_id (int): ID de la asignatura a la que pertenece la máquina virtual
        nombre (str): Nombre de la máquina virtual

        vnc_username (str): Nombre de usuario para la conexión VNC
        vnc_password (str): Contraseña para la conexión VNC

        is_base_vm (bool): Indica si la máquina virtual es base
        cloned_from (int): ID de la máquina virtual de la que se clonó
        created_at (datetime): Fecha de creación de la máquina virtual

        asignatura (Asignatura): Asignatura a la que pertenece la máquina virtual
        usuario (Usuario): Usuario propietario de la máquina virtual
    """
    __tablename__ = 'virtual_machines'

    proxmox_id = db.Column(db.Integer, nullable=False, primary_key=True)
    guacamole_connection_id = db.Column(db.Integer, nullable=True, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)

    vnc_username = db.Column(db.String(255), nullable=True)
    vnc_password = db.Column(db.Text, nullable=True)

    is_base_vm = db.Column(db.Boolean, default=False, nullable=False)
    cloned_from = db.Column(
        db.Integer,
        db.ForeignKey('virtual_machines.proxmox_id', ondelete='SET NULL'),
        nullable=True,
        index = True
    )
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    asignatura = db.relationship('Asignatura', back_populates='virtual_machines')
    usuario = db.relationship('Usuario', back_populates='virtual_machines')

    def set_vnc_password(self, vnc_password):
        """Cifra la contraseña VNC y la asigna al objeto

        :param vnc_password: Contraseña VNC
        :type vnc_password: str
        """
        cipher_suite = Fernet(key)
        self.vnc_password = cipher_suite.encrypt(vnc_password.encode()).decode()

    def get_vnc_password(self):
        """Descifra la contraseña VNC y la retorna

        :return: Contraseña VNC
        :rtype: str
        """
        cipher_suite = Fernet(key)
        return cipher_suite.decrypt(self.vnc_password.encode()).decode()

    def check_vnc_password(self, vnc_password):
        """Verifica si la contraseña VNC ingresada es correcta
        
        :param vnc_password: Contraseña VNC a verificar
        :type vnc_password: str

        :return: True si la contraseña es correcta, False en caso contrario
        :rtype: bool
        """
        cipher_suite = Fernet(key)
        return cipher_suite.decrypt(self.vnc_password.encode()).decode() == vnc_password

    def __init__(self, nombre, user_id, asignatura_id, proxmox_id, guacamole_connection_id=None, vnc_username=None, cloned_from=None, is_base_vm=False):
        """Constructor del modelo virtual_machines

        :param nombre: Nombre de la máquina virtual
        :type nombre: str

        :param user_id: ID del usuario dueño de la máquina virtual
        :type user_id: int

        :param asignatura_id: ID de la asignatura a la que pertenece la máquina virtual
        :type asignatura_id: int

        :param proxmox_id: ID de la máquina virtual en Proxmox
        :type proxmox_id: int

        :param guacamole_connection_id: ID de la conexión en Guacamole (default: None)
        :type guacamole_connection_id: int

        :param vnc_username: Nombre de usuario para acceder a la máquina virtual (default: None)
        :type vnc_username: str

        :param is_base_vm: Indica si la máquina virtual es base (default: False)
        :type is_base_vm: bool

        :param cloned_from: ID de la máquina virtual de la que se clonó (default: None)
        :type cloned_from: int
        """
        self.proxmox_id = proxmox_id
        self.nombre = nombre
        self.user_id = user_id
        self.asignatura_id = asignatura_id
        self.guacamole_connection_id = guacamole_connection_id # Se permite que sea nulo al crear la máquina.
        self.vnc_username = vnc_username
        self.is_base_vm = is_base_vm
        self.cloned_from = cloned_from

    def serialize(self):
        """Serializa el objeto virtual_machines a un diccionario

        :return: Diccionario con los datos de la máquina virtual
        :rtype: dict
        """
        return {
            'proxmox_id': self.proxmox_id,
            'guacamole_connection_id': self.guacamole_connection_id,
            'user_id': self.user_id,
            'asignatura_id': self.asignatura_id,
            'nombre': self.nombre,
            'is_base_vm': self.is_base_vm,
            'cloned_from': self.cloned_from,
            'created_at': self.created_at
        }

    def __repr__(self):
        """Representación de la máquina virtual como string

        :return: Representación de la máquina virtual
        :rtype: str
        """
        return f"VirtualMachine({self.nombre})"
