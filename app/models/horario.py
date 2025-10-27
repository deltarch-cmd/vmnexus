from app.extensions import db
from sqlalchemy.types import Enum

DAYS_OF_WEEK = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')

class Horario(db.Model):
    """Modelo de la tabla horarios en la base de datos

    Atributos:
        id (int): ID del horario
        dia (str): Día de la semana del horario
        hora_inicio (time): Hora de inicio del horario
        hora_fin (time): Hora de fin del horario
        asignatura_id (int): ID de la asignatura a la que pertenece el horario

        asignatura (Asignatura): Asignatura a la que pertenece el horario
    """
    __tablename__ = 'horarios'

    id = db.Column(db.Integer, primary_key=True)
    dia = db.Column(Enum(*DAYS_OF_WEEK, name='dia_semana'), nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id', ondelete='CASCADE'), nullable=False)

    asignatura = db.relationship('Asignatura', back_populates='horarios', lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('dia', 'hora_inicio', 'hora_fin', 'asignatura_id', name='uq_horario_por_asignatura'),
    )

    def __init__(self, dia, hora_inicio, hora_fin, asignatura_id):
        """Constructor del modelo horarios

        :param dia: Día de la semana del horario
        :type dia: str

        :param hora_inicio: Hora de inicio del horario
        :type hora_inicio: time

        :param hora_fin: Hora de fin del horario
        :type hora_fin: time

        :param asignatura_id: ID de la asignatura a la que pertenece el horario
        :type asignatura_id: int
        """
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.asignatura_id = asignatura_id

    def serialize(self):
        """Serializa el objeto horario a un diccionario

        :return: Diccionario con los datos del horario
        :rtype: dict
        """
        return {
            'id': self.id,
            'dia': self.dia,
            'hora_inicio': self.hora_inicio.strftime('%H:%M'),
            'hora_fin': self.hora_fin.strftime('%H:%M'),
            'asignatura_id': self.asignatura_id,
        }

    def __repr__(self):
        """Representación del horario como string

        :return: Representación del horario
        :rtype: str
        """
        return f"Horario({self.dia}, {self.hora_inicio}, {self.hora_fin})"
