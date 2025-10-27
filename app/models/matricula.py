from app.extensions import db
from datetime import datetime
# from app.models.usuario import Usuario
# from app.models.asignatura import Asignatura

class Matricula(db.Model):
    """Modelo de la tabla matriculas en la base de datos

    Atributos:
        user_id (int): ID del usuario matriculado
        asignatura_id (int): ID de la asignatura a la que se matriculó el usuario
        fecha_matricula (datetime): Fecha en la que se matriculó el usuario

        usuario (Usuario): Usuario matriculado
        asignatura (Asignatura): Asignatura a la que se matriculó el usuario
    """
    __tablename__ = 'matriculas'

    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), primary_key=True)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id', ondelete='CASCADE'), primary_key=True)
    fecha_matricula = db.Column(db.DateTime, default=datetime.now)

    usuario = db.relationship('Usuario', back_populates='matriculas', lazy='joined')
    asignatura = db.relationship('Asignatura', back_populates='matriculas', lazy='joined')

    __table_args__ = (
        db.PrimaryKeyConstraint('user_id', 'asignatura_id'),
    )

    def __init__(self, user_id, asignatura_id):
        """Constructor del modelo matriculas

        :param user_id: ID del usuario matriculado
        :type user_id: int

        :param asignatura_id: ID de la asignatura a la que se matriculó el usuario
        :type asignatura_id: int
        """
        self.user_id = user_id
        self.asignatura_id = asignatura_id

    def __repr__(self):
        """Representación de la matricula como string

        :return: Representación de la matricula
        :rtype: str
        """
        return f"Matricula({self.user_id}, {self.asignatura_id})"
