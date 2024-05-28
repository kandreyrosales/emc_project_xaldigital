from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship, sessionmaker
import enum
Base = declarative_base()


class TipoArticulo(enum.Enum):
    VIDEO = "video"
    TEXTO = "texto"


class Especializacion(Base):
    __tablename__ = 'especializaciones'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    bloque_id = Column(Integer, ForeignKey('bloques_de_cursos.id'))
    bloque = relationship('BloqueDeCursos', back_populates='especializacion', uselist=False)


class BloqueDeCursos(Base):
    __tablename__ = 'bloques_de_cursos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    description = Column(LONGTEXT)
    especializacion = relationship('Especializacion', back_populates='bloque', uselist=False)


class Residente(Base):
    __tablename__ = 'residentes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    progresos = relationship('Progreso', back_populates='residente')


class Curso(Base):
    __tablename__ = 'cursos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    bloque_id = Column(Integer, ForeignKey('bloques_de_cursos.id'))
    bloque = relationship('BloqueDeCursos', back_populates='cursos')
    articulos = relationship('Articulo', back_populates='curso')
    examen = relationship('Examen', uselist=False, back_populates='curso')


class Articulo(Base):
    __tablename__ = 'articulos'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    url = Column(String)  # Nuevo campo URL
    tipo = Column(Enum(TipoArticulo))  # Nuevo campo tipo
    curso_id = Column(Integer, ForeignKey('cursos.id'))
    curso = relationship('Curso', back_populates='articulos')
    progresos = relationship('Progreso', back_populates='articulo')

class Examen(Base):
    __tablename__ = 'examenes'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    curso_id = Column(Integer, ForeignKey('cursos.id'))
    curso = relationship('Curso', back_populates='examen')


class Progreso(Base):
    __tablename__ = 'progresos'
    id = Column(Integer, primary_key=True)
    residente_id = Column(Integer, ForeignKey('residentes.id'))
    articulo_id = Column(Integer, ForeignKey('articulos.id'), nullable=True)
    examen_id = Column(Integer, ForeignKey('examenes.id'), nullable=True)
    completado = Column(Boolean, default=False)
    residente = relationship('Residente', back_populates='progresos')
    articulo = relationship('Articulo', back_populates='progresos')
    examen = relationship('Examen')


def init_engine():
    db_name = "emc"
    db_user = "xaldigital"
    db_password = 'XalDigital!#388'
    engine = create_engine(f'postgresql://{db_user}:{db_password}@localhost:5432/{db_name}')
    return engine


def create_engine():
    Base.metadata.create_all(init_engine())


def insert_initial_data():
    Session = sessionmaker(bind=init_engine())
    session = Session()

    residente = Residente(email="kandreyrosales@gmail.com")

    especializacion = Especializacion(nombre="Cardio Neumología")
    bloque = BloqueDeCursos(nombre="Hipertensión Pulmonar",
                            especializacion=especializacion,
                            description="Explora los dilemas éticos en la práctica médica y desarrolla "
                                        "tu capacidad para tomar decisiones éticas y moralmente responsables "
                                        "en situaciones clínicas compleja")
    curso1 = Curso(nombre="Tratamiento HTPEC", bloque=bloque)
    curso2 = Curso(nombre="Tratamiento HP", bloque=bloque)
    curso3 = Curso(nombre="Diagnóstico", bloque=bloque)

    articulo1 = Articulo(nombre="Video 1", curso=curso1, tipo=TipoArticulo.VIDEO, url="https://www.youtube.com/watch?v=920XAV-n_vM&ab_channel=CursoCmedicaHpennaBahiaBlanca")
    articulo2 = Articulo(nombre="Archivo 1", curso=curso1, tipo=TipoArticulo.TEXTO, url="https://secardiologia.es/images/publicaciones/libros/cardiologia-hoy-2020.pdf")

    session.add(especializacion)
    session.add(bloque)
    session.add(residente)
    session.add(curso1)
    session.add(curso2)
    session.add(curso3)
    session.add(articulo1)
    session.add(articulo2)
    progreso1 = Progreso(residente=residente, articulo=articulo1, completado=True)
    progreso2 = Progreso(residente=residente, articulo=articulo2, completado=False)
    session.add(progreso1)
    session.add(progreso2)
    session.commit()


def get_emc_courses_data():
    response = {
        "specialty": "cardio neumología",
        "blocks": [
            {
                "name": "hipertensión pulmonar",
                "courses": [
                    {"name": "Tratamiento HTPEC", "id": 1, "description": "Explora los dilemas éticos en la práctica médica y desarrolla tu capacidad para tomar decisiones éticas y moralmente responsables en situaciones clínicas compleja"},
                    {"name": "Tratamiento HP", "id": 2, "description": "Explora los dilemas éticos en la práctica médica y desarrolla tu capacidad para tomar decisiones éticas y moralmente responsables en situaciones clínicas compleja"},
                    {"name": "Diagnostico", "id": 2, "description": "Explora los dilemas éticos en la práctica médica y desarrolla tu capacidad para tomar decisiones éticas y moralmente responsables en situaciones clínicas compleja"}
                ]
            }
        ]
    }






