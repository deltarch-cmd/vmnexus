from app.extensions import db

class Asignatura(db.Model):
    """Modelo de la tabla asignaturas en la base de datos

    Atributos:
        id (int): ID de la asignatura
        nombre (str): Nombre de la asignatura
        descripcion (str): Descripción de la asignatura
        profesor_id (int): ID del profesor que imparte la asignatura

        laboratorios (list[Laboratorio]): Lista de laboratorios asociados a la asignatura
        matriculas (list[Matricula]): Lista de matrículas asociadas a la asignatura
        horarios (list[Horario]): Lista de horarios asociados a la asignatura
        virtual_machines (list[VirtualMachine]): Lista de máquinas virtuales asociadas a la asignatura
    """
    __tablename__ = 'asignaturas'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    descripcion = db.Column(db.String(255), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    laboratorios = db.relationship('Laboratorio', back_populates='asignatura', cascade='all, delete-orphan', passive_deletes=True)
    matriculas = db.relationship('Matricula', back_populates='asignatura', cascade='all, delete-orphan', passive_deletes=True)
    horarios = db.relationship('Horario', back_populates='asignatura', cascade='all, delete-orphan', passive_deletes=True)
    virtual_machines = db.relationship('VirtualMachine', back_populates='asignatura', lazy='dynamic')

    def __init__(self, nombre, profesor_id, descripcion=None):
        """Constructor del modelo asignaturas

        :param nombre: Nombre de la asignatura
        :type nombre: str

        :param profesor_id: ID del profesor que imparte la asignatura
        :type profesor_id: int

        :param descripcion: Descripción de la asignatura (default: None)
        :type descripcion: str
        """
        self.nombre = nombre
        self.profesor_id = profesor_id
        self.descripcion = descripcion

    def serialize(self):
        """Serializa el objeto asignatura a un diccionario

        :return: Diccionario con los datos de la asignatura
        :rtype: dict
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'profesor_id': self.profesor_id,
        }

    def __repr__(self):
        """Representación de la asignatura como string

        :return: Representación de la asignatura
        :rtype: str
        """
        return f"Asignatura({self.nombre})"
