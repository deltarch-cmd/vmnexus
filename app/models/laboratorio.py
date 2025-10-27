from app.extensions import db
# from app.models.usuario import Usuario
# from app.models.asignatura import Asignatura

class Laboratorio(db.Model):
    """Modelo de la tabla laboratorios en la base de datos

    Atributos:
        id (int): ID del laboratorio
        nombre (str): Nombre del laboratorio
        asignatura_id (int): ID de la asignatura a la que pertenece el laboratorio
        pdf_url (str): URL del PDF con la guía del laboratorio
        profesor_id (int): ID del profesor que imparte el laboratorio

        asignatura (Asignatura): Asignatura a la que pertenece el laboratorio
    """
    __tablename__ = 'laboratorios'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id', ondelete='CASCADE'), nullable=False)
    pdf_url = db.Column(db.String(255), nullable=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    asignatura = db.relationship('Asignatura', back_populates='laboratorios', lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('nombre', 'asignatura_id', name='uq_laboratorio_nombre_asignatura_id'),
    )

    def __init__(self, nombre, asignatura_id, profesor_id, pdf_url=None):
        """Constructor del modelo laboratorios

        :param nombre: Nombre del laboratorio
        :type nombre: str

        :param asignatura_id: ID de la asignatura a la que pertenece el laboratorio
        :type asignatura_id: int

        :param profesor_id: ID del profesor que imparte el laboratorio
        :type profesor_id: int

        :param pdf_url: URL del PDF con la guía del laboratorio (default: None)
        :type pdf_url: str
        """
        self.nombre = nombre
        self.asignatura_id = asignatura_id
        self.profesor_id = profesor_id
        self.pdf_url = pdf_url

    def serialize(self, with_pdf_name=False):
        """Serializa el objeto laboratorio a un diccionario

        :param with_pdf_name: Indica si se debe incluir el nombre del PDF o la URL completa (default: False)
        :type with_pdf_name: bool

        :return: Diccionario con los datos del laboratorio
        :rtype: dict
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'asignatura_id': self.asignatura_id,
            'profesor_id': self.profesor_id,
            'pdf_url': None if not self.pdf_url else (
                self.pdf_url.split('/')[-1] if with_pdf_name else self.pdf_url
            )
        }

    def __repr__(self):
        """Representación del laboratorio como string
        
        :return: Representación del laboratorio
        :rtype: str
        """
        return f"Laboratorio({self.nombre})"
