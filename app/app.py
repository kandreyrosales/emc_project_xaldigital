from datetime import datetime
import json
import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON


db_username = os.getenv("db_username")
db_password = os.getenv("db_password")
db_endpoint = os.getenv("db_endpoint")
db_name = os.getenv("db_name")


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_username}:{db_password}@{db_endpoint}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configuración de Flask para asegurarse de que use UTF-8
app.config['JSON_AS_ASCII'] = False

db = SQLAlchemy(app)


class Especializacion(db.Model):
    __tablename__ = 'especializacion'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)


class BloqueCurso(db.Model):
    __tablename__ = 'bloque_curso'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text)
    especializacion_id = db.Column(db.Integer, db.ForeignKey('especializacion.id', ondelete='CASCADE'))
    especializacion = db.relationship('Especializacion', backref=db.backref('bloques_curso', lazy=True))


class Curso(db.Model):
    __tablename__ = 'curso'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text)
    bloque_curso_id = db.Column(db.Integer, db.ForeignKey('bloque_curso.id', ondelete='CASCADE'))
    bloque_curso = db.relationship('BloqueCurso', backref=db.backref('cursos', lazy=True))


class Articulo(db.Model):
    __tablename__ = 'articulo'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.Text, nullable=False)
    contenido = db.Column(db.Text)
    tipo = db.Column(db.String(50), nullable=False)
    url_contenido = db.Column(db.Text)
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id', ondelete='CASCADE'))
    curso = db.relationship('Curso', backref=db.backref('articulos', lazy=True))

    __table_args__ = (
        db.CheckConstraint(tipo.in_(['video', 'pdf']), name='check_tipo_valido'),
    )


class Examen(db.Model):
    __tablename__ = 'examen'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.Text, nullable=False)
    articulo_id = db.Column(db.Integer, db.ForeignKey('articulo.id', ondelete='CASCADE'))
    articulo = db.relationship('Articulo', backref=db.backref('examenes', lazy=True))


class Pregunta(db.Model):
    __tablename__ = 'pregunta'
    id = db.Column(db.Integer, primary_key=True)
    enunciado = db.Column(db.Text, nullable=False)
    opcion_a = db.Column(db.Text, nullable=False)
    opcion_b = db.Column(db.Text, nullable=False, default='Ninguna')
    opcion_c = db.Column(db.Text, nullable=False, default='Ninguna')
    opcion_d = db.Column(db.Text, nullable=False, default='Ninguna')
    respuesta_correcta = db.Column(db.String(1), nullable=False)  # 'A', 'B', 'C', 'D'
    explicacion = db.Column(db.Text, nullable=True)
    examen_id = db.Column(db.Integer, db.ForeignKey('examen.id', ondelete='CASCADE'))
    examen = db.relationship('Examen', backref=db.backref('preguntas', lazy=True))


class ResultadoExamen(db.Model):
    __tablename__ = 'resultado_examen'
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(255), nullable=False)
    examen_id = db.Column(db.Integer, db.ForeignKey('examen.id', ondelete='CASCADE'), nullable=False)
    puntaje = db.Column(db.Float, nullable=False)
    fecha_realizacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    tiempo_total = db.Column(db.Integer, nullable=False)
    examen = db.relationship('Examen', backref=db.backref('resultados_examen', lazy=True))
    respuestas = db.Column(JSON)


class PuntajeUsuarioExtraArticulos(db.Model):
    """
    Este modelo sirve para guardar puntaje cuando el usuario lea un PDF o termine un video, etc.
    """
    __tablename__ = 'puntaje_usuario'
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(255), nullable=False)
    puntaje = db.Column(db.Float, nullable=False)
    articulo_id = db.Column(db.Integer, db.ForeignKey('articulo.id', ondelete='CASCADE'))
    articulo = db.relationship('Articulo', backref=db.backref('puntajes_usuario', lazy=True))


def crear_examen(articulo_id, data_exam: dict):

    titulo = data_exam.get('titulo')
    preguntas_data = data_exam.get('preguntas', [])

    if not titulo or not preguntas_data:
        return jsonify({'message': 'Titulo del examen y preguntas son requeridos'}), 400

    # Crear el examen
    nuevo_examen = Examen(titulo=titulo, articulo_id=articulo_id)
    db.session.add(nuevo_examen)
    db.session.commit()

    # Crear las preguntas asociadas al examen
    for pregunta_data in preguntas_data:
        enunciado = pregunta_data.get('enunciado')
        opcion_a = pregunta_data.get('opcion_a')
        opcion_b = pregunta_data.get('opcion_b')
        opcion_c = pregunta_data.get('opcion_c')
        opcion_d = pregunta_data.get('opcion_d')
        respuesta_correcta = pregunta_data.get('respuesta_correcta')
        explicacion = pregunta_data.get('explicacion')

        nueva_pregunta = Pregunta(
            enunciado=enunciado,
            opcion_a=opcion_a,
            opcion_b=opcion_b,
            opcion_c=opcion_c,
            opcion_d=opcion_d,
            respuesta_correcta=respuesta_correcta,
            examen_id=nuevo_examen.id,
            explicacion=explicacion
        )
        db.session.add(nueva_pregunta)
    db.session.commit()
    return jsonify({'message': 'Examen creado exitosamente'}), 201


def create_tables():
    with app.app_context():
        db.create_all()
        print("All tables created.")


def drop_tables():
    with app.app_context():
        db.drop_all()
        print("All tables dropped.")


def insert_initial_data():
    drop_tables()
    create_tables()
    with app.app_context():
        # Por ahora tendremos dos especialidades
        especializacion_cardio = Especializacion(nombre='Cardio Neumología')
        especializacion_hematologia = Especializacion(nombre='Hematología')
        db.session.add(especializacion_cardio)
        db.session.add(especializacion_hematologia)

        # Bloques
        hipertension_bloque = BloqueCurso(
            nombre="Hipertensión Pulmonar",
            especializacion=especializacion_cardio,
            contenido="Este curso intensivo le brinda una comprensión profunda de la HTP, "
                      "una condición compleja que afecta los pulmones. Explore las causas, "
                      "la clasificación, el diagnóstico y las opciones de tratamiento, "
                      "incluyendo medicamentos, procedimientos quirúrgicos y cuidados de apoyo.")
        hemofilia_bloque = BloqueCurso(
            nombre="Comprenda a fondo la Hemofilia",
            especializacion=especializacion_hematologia,
            contenido="Mejore su comprensión de esta condición compleja para brindar "
                      "una atención informada a los pacientes.")
        db.session.add(hipertension_bloque)
        db.session.add(hemofilia_bloque)

        # cursos HEMOFILIA
        curso_jivi = Curso(
            nombre="JIVI (DAMOCTOCOG ALFA PEGOL)",
            bloque_curso=hemofilia_bloque,
            contenido="Este curso es intermedio")
        db.session.add(curso_jivi)
        curso_kovaltry = Curso(
            nombre="KOVALTRY (OCTOCOG ALFA)",
            bloque_curso=hemofilia_bloque,
            contenido="Este curso es inicial")
        db.session.add(curso_kovaltry)
        # curso Hipertension pulmonar
        curso_hipertension = Curso(
            nombre="Hipertensión Pulmonar",
            bloque_curso=hipertension_bloque,
            contenido="Este curso es inicial")
        db.session.add(curso_hipertension)

        # articulos KOVALTRY
        articulo_kovaltry = Articulo(
            titulo="Factor VIII q3 tarjeton famacocinética",
            contenido='PDF sobre Factor VIII q3 tarjeton famacocinética',
            tipo='pdf',
            url_contenido='https://archivosemc.s3.amazonaws.com/FactorVIII+Q3+Tarjeton+Farmacocinetica_HIGH.pdf',
            curso=curso_kovaltry
        )
        data_examen_kovaltry_1 = {
            "titulo": "Examen Factor VIII q3 tarjeton famacocinética",
            "preguntas": [
                {
                    "enunciado": "¿Cuál es la principal ventaja de Kovaltry® sobre Advate® en términos de vida media de la actividad de FVIII?",
                    "opcion_a": "Kovaltry® reduce la vida media en un 23%.",
                    "opcion_b": "Kovaltry® prolonga la vida media en un 23%.",
                    "opcion_c": "Kovaltry® no afecta la vida media de FVIII.",
                    "respuesta_correcta": "B",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Cuánto incrementa Kovaltry® la mediana del tiempo de actividad de FVIII >1 U/dl respecto de Advate®?",
                    "opcion_a": "10-12 horas",
                    "opcion_b": "18-20 horas",
                    "opcion_c": "25-30 horas",
                    "respuesta_correcta": "B",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿En cuántas veces incrementa Kovaltry® la proporción de personas con hemofilia A grave que mantienen actividad de FVIII >1 U/dl en comparación con Advate®?",
                    "opcion_a": "1.5 veces",
                    "opcion_b": "2.0 veces",
                    "opcion_c": "2.67 veces",
                    "respuesta_correcta": "C",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Cuál es la relación de la dosis requerida de Kovaltry® para mantener la actividad de FVIII >1 U/dl respecto a Advate® cuando se administra dos veces por semana?",
                    "opcion_a": "0.33",
                    "opcion_b": "0.50",
                    "opcion_c": "0.67",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "Según los estudios citados, ¿cuál es el porcentaje de personas con hemofilia A grave que mantienen actividad de FVIII >1 U/dl con Kovaltry®?",
                    "opcion_a": "18.4%",
                    "opcion_b": "49.2%",
                    "opcion_c": "74.5%",
                    "respuesta_correcta": "B",
                    "explicacion": ""
                },
            ]
        }

        articulo_kovaltry_2 = Articulo(
            titulo="Factor VIII q4 latest taurus",
            contenido='PDF sobre Factor VIII q4 latest taurus',
            tipo='pdf',
            url_contenido='https://archivosemc.s3.amazonaws.com/FactorVIII+Q4+Latest+Taurus.pdf',
            curso=curso_kovaltry
        )
        data_examen_kovaltry_2 = {
            "titulo": "Examen Factor VIII q4 latest taurus",
            "preguntas": [
                {
                    "enunciado": "¿Cuál fue el objetivo principal del estudio de fase IV TAURUS?",
                    "opcion_a": "Investigar la efectividad de un nuevo medicamento para la hemofilia",
                    "opcion_b": "Evaluar los regímenes de profilaxis con Kovaltry® en la práctica clínica diaria en individuos con hemofilia A moderada-grave.",
                    "opcion_c": "Comparar los efectos secundarios de Kovaltry® con otros tratamientos para la diabetes.",
                    "respuesta_correcta": "B",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Qué proporción de sujetos con hemofilia A tratados con ≤2 infusiones semanales aumentó después de 12 meses de tratamiento con Kovaltry®?",
                    "opcion_a": "De 27% a 38%",
                    "opcion_b": "De 30% a 45%",
                    "opcion_c": "De 20% a 35%",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Cuál fue el perfil de seguridad de Kovaltry® en el estudio TAURUS?",
                    "opcion_a": "56 eventos adversos emergentes al tratamiento en 18% de los participantes.",
                    "opcion_b": "70 eventos adversos graves en 50% de los participantes.",
                    "opcion_c": "No se reportaron eventos adversos.",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Qué ventaja se observó en la profilaxis con Kovaltry® respecto a la satisfacción y adherencia al tratamiento?",
                    "opcion_a": "Reducción en la satisfacción de los pacientes.",
                    "opcion_b": "Altos niveles de satisfacción y adherencia al tratamiento.",
                    "opcion_c": "No hubo cambios en la satisfacción y adherencia al tratamiento.",
                    "respuesta_correcta": "B",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Cuál es el beneficio del perfil farmacocinético de Kovaltry® en comparación con productos estándar de FVIII como Kogenate® y Advate®?",
                    "opcion_a": "Menor tiempo de actividad del FVIII por encima del umbral >1 U/dl.",
                    "opcion_b": "Mayor tiempo de actividad del FVIII por encima del umbral >1 U/dl.",
                    "opcion_c": "No hay diferencia en el tiempo de actividad del FVIII.",
                    "respuesta_correcta": "B",
                    "explicacion": ""
                }
            ]
        }

        # articulos JIVI (DAMOCTOCOG ALFA PEGOL)
        articulo_jivi = Articulo(
            titulo="Recombinant factor VIII with an extended half-life, in subjects with hemophilia A",
            contenido='Este material trata de un PDF muy importante',
            tipo='pdf',
            url_contenido='https://archivosemc.s3.amazonaws.com/2.+JIVI%C2%AE+%5Bfactor+antihemofi%CC%81lico+(recombinante)%2C+PEGilado-aucl%5D+polvo+liofilizado.pdf',
            curso=curso_jivi
        )
        data_examen_jivi_1 = {
            "titulo": "Examen Recombinant factor VIII",
            "preguntas": [
                {
                    "enunciado": "¿Qué han sugerido los estudios observacionales en pacientes con hemofilia A con respecto a la terapia profiláctica de reemplazo de factor?",
                    "opcion_a": "Es menos eficaz que el tratamiento a demanda para prevenir episodios de sangrado articular.",
                    "opcion_b": "Es más eficaz que el tratamiento a demanda para prevenir episodios de sangrado articular y retardar la progresión de la artropatía.",
                    "opcion_c": "No tiene diferencia significativa respecto al tratamiento a demanda para episodios de sangrado articular.",
                    "respuesta_correcta": "B",
                    "explicacion": "Es más eficaz que el tratamiento a demanda para prevenir episodios de sangrado articular y retardar la progresión de la artropatía."
                },
                {
                    "enunciado": "¿Cuáles son algunos de los desafíos de la profilaxis en la práctica diaria?",
                    "opcion_a": "Bajo coste y facilidad de venopunción",
                    "opcion_b": "Alto costo, dificultades con la venopunción y complicaciones de los dispositivos de acceso venoso.",
                    "opcion_c": "No se reportaron desafíos significativos.",
                    "respuesta_correcta": "B",
                    "explicacion": "Alto costo, dificultades con la venopunción y complicaciones de los dispositivos de acceso venoso."
                },
                {
                    "enunciado": "¿Cuál es un beneficio potencial de una terapia de reemplazo de FVIII con una vida media más larga?",
                    "opcion_a": "Podría aumentar la frecuencia de los intervalos de tratamiento.",
                    "opcion_b": "Podría reducir las cargas asociadas con la profilaxis y mejorar los resultados clínicos.",
                    "opcion_c": "Podría hacer que la profilaxis requiera más tiempo.",
                    "respuesta_correcta": "B",
                    "explicacion": "Podría reducir las cargas asociadas con la profilaxis y mejorar los resultados clínicos."
                },
                {
                    "enunciado": "¿Qué hicieron Mei et al. describen en su estudio sobre la PEGilación del FVIII?",
                    "opcion_a": "Un método que utiliza metilación de lisina que disminuyó la actividad de coagulación.",
                    "opcion_b": "Una estrategia novedosa que utiliza mutagénesis dirigida al sitio para modificar BDD-rFVIII. ",
                    "opcion_c": "Un método ineficaz para prolongar la vida media del FVIII.",
                    "respuesta_correcta": "B",
                    "explicacion": "Una estrategia novedosa que utiliza mutagénesis dirigida para modificar BDD-rFVIII."
                },
                {
                    "enunciado": "¿Cuál fue el resultado del primer estudio en humanos de BAY 94-9027 con respecto a la seguridad?",
                    "opcion_a": "Varios sujetos desarrollaron anticuerpos inhibidores contra el FVIII.",
                    "opcion_b": "BAY 94-9027 fue bien tolerado y no se detectaron anticuerpos inhibidores o no inhibidores.",
                    "opcion_c": "Se observaron cambios significativos en los parámetros de laboratorio clínico.",
                    "respuesta_correcta": "B",
                    "explicacion": "BAY 94-9027 fue bien tolerado y no se detectaron anticuerpos inhibidores o no inhibidores."
                }
            ]
        }
        articulo_jivi_2 = Articulo(
            titulo='Immunogenicity of long-lasting recombinant factor VIII products',
            contenido='Este material trata de un PDF muy importante',
            tipo='pdf',
            url_contenido='https://archivosemc.s3.amazonaws.com/4.+Immunogenicity+of+long+recombinant.pdf',
            curso=curso_jivi
        )
        data_examen_jivi_2 = {
            "titulo": "Examen JIVI Immunogenicity of long-lasting recombinant factor VIII products",
            "preguntas": [
                {
                    "enunciado": "¿Cuál ha sido uno de los principales beneficios del factor terapéutico VIII (FVIII) de nueva generación para los pacientes con hemofilia A?",
                    "opcion_a": "Ha eliminado la necesidad de cualquier tratamiento profiláctico.",
                    "opcion_b": "Ha mejorado significativamente la calidad de vida de los pacientes hemofílicos.",
                    "opcion_c": "Ha reducido la aparición de infecciones virales en los pacientes.",
                    "respuesta_correcta": "B",
                    "explicacion": "Ha mejorado significativamente la calidad de vida de los pacientes hemofílicos."
                },
                {
                    "enunciado": "¿Cuál es un desafío importante asociado con la corta vida media del FVIII?",
                    "opcion_a": "Requiere administraciones frecuentes, lo que lleva a una adherencia limitada del paciente.",
                    "opcion_b": "Provoca una mayor inmunogenicidad y efectos secundarios más graves. ",
                    "opcion_c": "Conduce a un mayor riesgo de infecciones virales debido a la dosificación frecuente. ",
                    "respuesta_correcta": "A",
                    "explicacion": "Requiere administraciones frecuentes, lo que lleva a una adherencia limitada del paciente."
                },
                {
                    "enunciado": "¿Qué estrategia se menciona para extender la vida media del FVIII terapéutico?",
                    "opcion_a": "Acoplamiento de FVIII a fragmentos Fc diméricos de inmunoglobulina G humana.",
                    "opcion_b": "Aumentar la frecuencia de dosificación de las infusiones de FVIII. ",
                    "opcion_c": "Utilizar únicamente infusiones de sangre total y crioprecipitado. ",
                    "respuesta_correcta": "A",
                    "explicacion": "Acoplamiento de FVIII a fragmentos Fc diméricos de inmunoglobulina G humana."
                },
                {
                    "enunciado": "¿Qué porcentaje de pacientes con hemofilia A grave desarrollan anticuerpos IgG anti-FVIII después de la terapia de reemplazo?",
                    "opcion_a": "Hasta el 10%.",
                    "opcion_b": "Hasta el 20%.",
                    "opcion_c": "Hasta el 30%.",
                    "respuesta_correcta": "C",
                    "explicacion": "Hasta el 30%."
                },
                {
                    "enunciado": "¿Cuál es un problema potencial con el uso de polietilenglicol (PEG) en productos de FVIII?",
                    "opcion_a": " El PEG es altamente antigénico y provoca reacciones inmunitarias graves.",
                    "opcion_b": "El PEG puede provocar alteraciones histológicas en diversos órganos debido a su acumulación.",
                    "opcion_c": "PEG no afecta la vida media del FVIII de manera significativa.",
                    "respuesta_correcta": "B",
                    "explicacion": "El PEG puede provocar alteraciones histológicas en diversos órganos debido a su acumulación"
                }
            ]
        }

        # articulos Hipertension pulmonar
        articulo_hipertension_1 = Articulo(
            titulo="E-Detailing Compendium Adempas 2023",
            contenido='PDF sobre E-Detailing Compendium Adempas 2023',
            tipo='pdf',
            url_contenido='https://archivosemc.s3.amazonaws.com/E-Detailing+Compendium+Adempas+2023+(Aprobada).pdf',
            curso=curso_hipertension
        )
        data_examen_hipertension_1 = {
            "titulo": "Examen JIVI 1",
            "preguntas": [
                {
                    "enunciado": "¿Qué estimula el riociguat?",
                    "opcion_a": "Guanilato ciclasa soluble",
                    "opcion_b": "Guanilito ciclasa insoluble",
                    "opcion_c": "Ninguna de las anteriores",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Qué es la GCs?",
                    "opcion_a": "Enzima que se encuentra en las células endoteliales de las arterias pulmonares",
                    "opcion_b": "Enzima que se encuentra en las céulas endoteliales de las arterias cardiacas",
                    "opcion_c": "Molécula que se encuentra en las células sanguíneas",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Cuales son algunas de las determinantes de progresión o estimadores de moralidad a 1 año?",
                    "opcion_a": "Marcadores bioquimicos, síncope, capadidad de ejercicio y evaluación de hemodinámica",
                    "opcion_b": "IMC, anemia, capacidad de ejercicio",
                    "opcion_c": "Test neurológico, hemodinámica y marcadores hepáticos",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "DPC6M 165-440m, BNP 50-800 ng/L, FEVD 37-54% y IVS 31-38 son caracteristicas de un paciente con riesgo",
                    "opcion_a": "Intermedio",
                    "opcion_b": "Bajo",
                    "opcion_c": "Alto",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "Falla cardiaca derecha ausente, DPC6M >440m, BNP <50 ng/L, FEVD >54% y IVS >38 son caracteristicas de un paciente con riesgo",
                    "opcion_a": "Bajo",
                    "opcion_b": "Intermedio",
                    "opcion_c": "Alto",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
            ]
        }
        articulo_hipertension_2 = Articulo(
            titulo="HIPERTENSIÓN PULMONAR TROMBOEMBOLICA (HTPEC)",
            contenido='Video sobre HIPERTENSIÓN PULMONAR TROMBOEMBOLICA (HTPEC)',
            tipo='video',
            url_contenido='https://archivosemc.s3.amazonaws.com/Resphirablastos+Tratamiento+en+HTPEC+(Dra.+N.Zayas).mp4',
            curso=curso_hipertension
        )
        data_examen_hipertension_2 = {
            "titulo": "Examen HIPERTENSIÓN PULMONAR TROMBOEMBOLICA (HTPEC)",
            "preguntas": [
                {
                    "enunciado": "¿Cual es una de las carácterísticas patológcas de la HPTEPC?",
                    "opcion_a": "Material tromboembólico organizado y remodelación vascular por combinación de angiogenesis defectusa y disfucnión endotelial",
                    "opcion_b": "Material tromboembólico desorganizado por combinación de disfunción epitelial",
                    "opcion_c": "Material tromboembólico por mala alimentación y estilo de vida poco saludable",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿Cual es una de las principales diferencias entre enfermedad tromnboembolica sin hipertensión pulmonar y con hipertensión pulmonar?",
                    "opcion_a": "Disnea en el descanso",
                    "opcion_b": "Disnea en el ejercicio",
                    "opcion_c": "Periodo de tratamiento con anticoagulantes",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "¿El gamagrama es la prueba definitoria para diagnosticar a los pacientes con HPTEC?",
                    "opcion_a": "No, se debe tener sus reservas y complementar con otros estudios",
                    "opcion_b": "Sí, es la prueba diagnóstica por excelencia",
                    "opcion_c": "El gamagrama no se debe hacer en pacientes con sospecha de HPTEC",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "Características para diferenciar la enfermedad cuando es aguda",
                    "opcion_a": "Infartos pulmonares y oclusión total",
                    "opcion_b": "Defectos periféricos",
                    "opcion_c": "Atenuación en mosaico",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "Características para diferenciar la enfermedad cuando es crónica",
                    "opcion_a": "Vasos colaterales y calcificación",
                    "opcion_b": "Oclusión total",
                    "opcion_c": "Defectos centrales",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
            ]
        }

        articulo_hipertension_3 = Articulo(
            titulo="HIPERTENSIÓN ARTERIAL PULMONAR (HAP)",
            contenido='Video sobre HIPERTENSIÓN ARTERIAL PULMONAR (HAP)',
            tipo='video',
            url_contenido='https://archivosemc.s3.amazonaws.com/Resphirablastos+Tratamiento+HP+(Dr.T.Pulido).mp4',
            curso=curso_hipertension
        )
        data_examen_hipertension_3 = {
            "titulo": "Examen HIPERTENSIÓN ARTERIAL PULMONAR (HAP)",
            "preguntas": [
                {
                    "enunciado": "Son Criterios para diagnoticar HAP",
                    "opcion_a": "HP precapilar: PAPm >20mmHg, PCP < 15mmHg y RVP > 2 UV",
                    "opcion_b": "Presión pulmonar media normal 14 +/- 3.3 mmHg",
                    "opcion_c": "HP precapilar: PAPm <20mmHg, PCP > 15mmHg y RVP < 2 UV",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "La HAP es progresiva, por lo tanto, de fase asintomática a fase terminal los síntomas son",
                    "opcion_a": "Aumento en la poscarga del VD, remodelamiento del miocardio hasta la falla cardiaca derecha aguda",
                    "opcion_b": "Aumento en el estrés de la pared del VD, falla cardiaca aguda hasta la dilatación del VD e insuficiencia cardiaca",
                    "opcion_c": "Insuficiencia cardiaca, aumento en el estrés de la pared del VD hasta la falla cardiaca aguda",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "De acuerdo a la estratificación del riesgo, los pacientes con riesgo alto presentan",
                    "opcion_a": "Signos de IC derecha, síncope repetido, progresión de síntomas rápida, PAD: >14 mmHg",
                    "opcion_b": "Síncope ocasional, derrame pericárdico mínimo, PAD: 8-14mmHG",
                    "opcion_c": "PAD: <8 mmHg, signos de IC derecha ausentes, BNP <50ng/L",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },
                {
                    "enunciado": "Para los pacientes con riesgo intermedio alto o alto se debe tratar de la siguiente manera",
                    "opcion_a": "Agregar APC i.v.  S..c y/o evaluar para trasplante pulmonar",
                    "opcion_b": "Continuar con tratamiento inicial",
                    "opcion_c": "Cambiar de iPDE5 a sGCs",
                    "opcion_d": "Todas las anteriores",
                    "respuesta_correcta": "A",
                    "explicacion": ""
                },

            ]
        }

        db.session.add(articulo_jivi)
        db.session.add(articulo_kovaltry)
        db.session.add(articulo_kovaltry_2)
        db.session.add(articulo_jivi_2)
        db.session.add(articulo_hipertension_1)
        db.session.add(articulo_hipertension_2)
        db.session.add(articulo_hipertension_3)

        crear_examen(articulo_kovaltry.id, data_examen_kovaltry_1)
        crear_examen(articulo_kovaltry_2.id, data_examen_kovaltry_2)
        crear_examen(articulo_jivi.id, data_examen_jivi_1)
        crear_examen(articulo_jivi_2.id, data_examen_jivi_2)
        crear_examen(articulo_hipertension_1.id, data_examen_hipertension_1)
        crear_examen(articulo_hipertension_2.id, data_examen_hipertension_2)
        crear_examen(articulo_hipertension_3.id, data_examen_hipertension_3)
        db.session.commit()


def connect_and_execute(query):
    try:
        # Connect to the database
        with app.app_context():
            result = db.session.execute(query)
            db.session.commit()  # Commit changes to the database
            return result
    except Exception as e:
        print(f"Error: {e}")
        return None


def obtener_cursos_por_especializacion(especializacion: str):
    especializacion_query = Especializacion.query.filter_by(nombre=especializacion).first()
    cursos = []
    if especializacion_query:
        for bloque in especializacion_query.bloques_curso:
            cursos.extend(bloque.cursos)
    return cursos


@app.route('/list_courses', methods=['GET'])
def list_courses():
    bloque_id = int(request.args.get('bloque_id'))
    bloque = BloqueCurso.query.filter_by(id=bloque_id).first()
    cursos_json = []
    if bloque:
        for curso in bloque.cursos:
            cursos_json.append({
                "id": curso.id,
                "nombre": curso.nombre,
                "contenido": curso.contenido
            })
    return jsonify(cursos_json)


def get_especialty(especializacion_nombre: str):
    especializacion_query = Especializacion.query.filter_by(nombre=especializacion_nombre).first()
    return especializacion_query


def percentage_course_finished(email_usuario:str, cursos: list):
    total_courses = len(cursos)
    exams_finished = 0
    for curso in cursos:
        curso_id = curso.id
        # Obtener todos los exámenes del curso
        examenes_curso = db.session.query(Examen.id).join(Articulo).filter(
            Articulo.curso_id == curso_id
        ).all()
        if not examenes_curso:
            continue
        examenes_curso_ids = {examen.id for examen in examenes_curso}

        # Obtener todos los exámenes realizados por el usuario
        examenes_usuario = db.session.query(ResultadoExamen.examen_id).filter_by(
            usuario_email=email_usuario
        ).all()
        examenes_usuario_ids = {examen.examen_id for examen in examenes_usuario}

        # Verificar si todos los exámenes del curso fueron realizados por el usuario
        if examenes_usuario:
            todos_examenes_realizados = examenes_curso_ids.issubset(examenes_usuario_ids)
            if todos_examenes_realizados:
                exams_finished += 1
    return exams_finished/total_courses if total_courses else 0


@app.route('/list_blocks', methods=['GET'])
def list_blocks():
    especializacion_nombre = request.args.get('especializacion_nombre')
    user_email = request.args.get('userEmail')
    especializacion_query = get_especialty(especializacion_nombre=especializacion_nombre)
    bloques_json = []
    if especializacion_query:
        for bloque in especializacion_query.bloques_curso:
            percentage_completed = percentage_course_finished(cursos=bloque.cursos, email_usuario=user_email)
            bloques_json.append({
                "nombre": bloque.nombre,
                "id": bloque.id,
                "contenido": bloque.contenido,
                "porcentaje_completado": percentage_completed,
                "porcentaje_completado_texto": f"{int(percentage_completed*100)}%"
            })
    return jsonify({"blocks": bloques_json})


@app.route('/create_tables_command', methods=['GET'])
def create_tables_command():
    create_tables()
    return jsonify({"message": "Tables created."})


@app.route('/drop_tables_command', methods=['GET'])
def drop_tables_command():
    drop_tables()
    return jsonify({"message": "Tables created."})


@app.route('/initial_data', methods=['GET'])
def initial_data():
    insert_initial_data()
    return jsonify({"message": "Initial Data created."})


@app.route('/list_specialties', methods=['GET'])
def list_specialties():
    especializaciones = Especializacion.query.all()
    especializaciones_json = []
    for especializacion in especializaciones:
        especializaciones_json.append({
            'id': especializacion.id,
            'nombre': especializacion.nombre,
        })
    return jsonify(especializaciones_json)


@app.route('/list_articles', methods=['GET'])
def list_articles():
    course_id = int(request.args.get('course_id'))
    articles = Articulo.query.filter_by(curso_id=course_id)
    articles_json = []
    for article in articles:
        articles_json.append({
            'id': article.id,
            'titulo': article.titulo,
            'url_file': article.url_contenido,
            'tipo': article.tipo,
            'contenido': article.contenido
        })
    return jsonify(articles_json)


@app.route('/article', methods=['GET'])
def get_article():
    """
    Un Articulo puede tener a futuro varios examanes, pero nosotros estaremos por ahora tomando solo 1
    :return:
    """
    article_id = int(request.args.get('article_id'))
    article = Articulo.query.get_or_404(article_id)
    return jsonify({
        'id': article.id,
        'titulo': article.titulo,
        'url_file': article.url_contenido,
        'tipo': article.tipo,
        'contenido': article.contenido,
        'examen_id': article.examenes[0].id,
    })


@app.route('/exam', methods=['GET'])
def get_examen():
    examen = Examen.query.get_or_404(int(request.args.get('exam_id')))
    if examen:
        return jsonify({
            'id': examen.id,
            'titulo': examen.titulo,
            'cantidad_preguntas': len(examen.preguntas),
            'preguntas_id': [pregunta.id for pregunta in examen.preguntas],
        })
    return jsonify({})


@app.route('/question', methods=['GET'])
def get_question():
    pregunta = Pregunta.query.get_or_404(int(request.args.get('question_id')))
    return jsonify({
        'id': pregunta.id,
        'enunciado': pregunta.enunciado,
        'opciones': [
            {'opcion': 'A', 'descripcion': pregunta.opcion_a},
            {'opcion': 'B', 'descripcion': pregunta.opcion_b},
            {'opcion': 'C', 'descripcion': pregunta.opcion_c},
            {'opcion': 'D', 'descripcion': pregunta.opcion_d},
        ],
        'respuesta_correcta': pregunta.respuesta_correcta,
        'explicacion':  pregunta.explicacion
    })


def check_correct_answer(question_id: int) -> str:
    pregunta = Pregunta.query.get_or_404(question_id)
    if pregunta.respuesta_correcta == 'A':
        return pregunta.opcion_a
    elif pregunta.respuesta_correcta == 'B':
        return pregunta.opcion_b
    elif pregunta.respuesta_correcta == 'C':
        return pregunta.opcion_c
    else:
        return pregunta.opcion_d


class Score:
    def __init__(self, questions: list, exam_id: int, user_email: str, elapsed_time: int):
        self.questions = questions
        self.results_id = None
        self.exam = Examen.query.get_or_404(exam_id)
        self.user_email = user_email
        self.elapsed_time = elapsed_time//60
        self.final_score = 0
        exam_result = self.validate_questions()
        self.exam_result = exam_result
        self.final_score = exam_result.get('points')
        self.save_score()

    def save_score(self):
        """
        Si ya existe un resultado anteror, entonces lo actualizamos con el ultimo puntaje y tiempo obtenido
        """
        last_exam_result = ResultadoExamen.query.filter_by(
            usuario_email=self.user_email,
            examen_id=self.exam.id).first()
        if last_exam_result:
            last_exam_result.tiempo_total = self.elapsed_time
            last_exam_result.puntaje = self.final_score
            last_exam_result.fecha_realizacion = datetime.utcnow()
            last_exam_result.respuestas = self.exam_result
            db.session.commit()
            self.results_id = last_exam_result.id
        else:
            resultado = ResultadoExamen(
                usuario_email=self.user_email,
                examen_id=self.exam.id,
                tiempo_total=self.elapsed_time,
                puntaje=self.final_score,
                respuestas=self.exam_result
            )
            db.session.add(resultado)
            db.session.commit()
            self.results_id = resultado.id

    def validate_questions(self):
        valid_answers = 0
        invalid_answers = 0
        json_list = []
        total_questions = len(self.questions)
        for question in self.questions:
            question_id = question.get('questionId')
            question_obj = Pregunta.query.get_or_404(question_id)
            user_option_selected = question.get('optionSelectedValue')
            if user_option_selected == question_obj.respuesta_correcta:
                valid_answers += 1
                json_list.append({
                    'enunciado_pregunta': question_obj.enunciado,
                    'respuesta_correcta': question_obj.respuesta_correcta,
                    'respuesta': 'correcta'
                })
            else:
                invalid_answers += 1
                json_list.append({
                    'enunciado_pregunta': question_obj.enunciado,
                    'respuesta_correcta': check_correct_answer(question_id=question_id),
                    'respuesta': 'incorrecta'
                })
        return {
            'questions': json_list,
            'valid_questions': valid_answers,
            'invalid_questions': invalid_answers,
            'points': (valid_answers/total_questions)*100
        }


@app.route('/send_exam_results', methods=['POST'])
def send_exam_results():
    data = request.json
    exam_results = data.get('exam_results')
    elapsed_time = data.get('elapsedTime')
    exam_id = data.get('examId')
    user_email = data.get('userEmail')
    score = Score(questions=exam_results, exam_id=exam_id, user_email=user_email, elapsed_time=elapsed_time)
    return jsonify({'exam_results_id': score.results_id})


@app.route('/exam_result', methods=['GET'])
def exam_result():
    exam_result_obj = ResultadoExamen.query.get_or_404(int(request.args.get('exam_result_id')))
    if exam_result_obj:
        return jsonify({
            'id': exam_result_obj.id,
            'result_responses': exam_result_obj.respuestas,
            'total_questions': len(exam_result_obj.respuestas.get('questions'))
        })
    return jsonify({})


@app.route('/extra_points', methods=['POST'])
def extra_points():
    data = request.json
    articulo_id = data.get('articleId')
    email = data.get('userEmail')
    article = Articulo.query.get_or_404(articulo_id)
    if article.tipo == "video":
        puntaje = 100
    else:
        puntaje = 60
    ultimo_puntaje = PuntajeUsuarioExtraArticulos.query.filter_by(
        usuario_email=email, articulo_id=articulo_id).first()
    if not ultimo_puntaje:
        puntaje_usuario = PuntajeUsuarioExtraArticulos(
            usuario_email=email,
            articulo_id=articulo_id,
            puntaje=puntaje
        )
        db.session.add(puntaje_usuario)
        db.session.commit()
        return jsonify({"message": f'Ganaste {puntaje} puntos por acceder a este contenido!', "extrapoints": True})
    return jsonify({"message": 'Ya tienes puntos por este contenido', "extrapoints": False})


def listar_cursos_por_usuario(email_usuario):
    cursos = db.session.query(Curso).join(Articulo).join(Examen).join(ResultadoExamen).filter(
        ResultadoExamen.usuario_email == email_usuario
    ).distinct().all()
    return cursos


def usuario_realizo_todos_los_examenes_de_curso(email_usuario:str, cursos):
    for curso in cursos:
        curso_id = curso.id
        # Obtener todos los exámenes del curso
        examenes_curso = db.session.query(Examen.id).join(Articulo).filter(
            Articulo.curso_id == curso_id
        ).all()
        examenes_curso_ids = {examen.id for examen in examenes_curso}

        # Obtener todos los exámenes realizados por el usuario
        examenes_usuario = db.session.query(ResultadoExamen.examen_id).filter_by(
            usuario_email=email_usuario
        ).all()
        examenes_usuario_ids = {examen.examen_id for examen in examenes_usuario}

        # Verificar si todos los exámenes del curso fueron realizados por el usuario
        todos_exámenes_realizados = examenes_curso_ids.issubset(examenes_usuario_ids)
        if todos_exámenes_realizados:
            return True
    return False


@app.route('/calculate_badges', methods=['GET'])
def calculate_badges():
    email = request.args.get('userEmail')
    badges = []
    total_badges = 30
    resultado_examen = ResultadoExamen.query.filter_by(usuario_email=email).first()
    if resultado_examen:
        badges.append({
            "name": "Principiante",
            "description": "Has completado tu primer examen!",
            "level": 1
        })
    if resultado_examen:
        # Listar cursos por usuario
        cursos = listar_cursos_por_usuario(email)
        if usuario_realizo_todos_los_examenes_de_curso(email, cursos):
            badges.append({
                "name": "Estudioso",
                "description": "Has completado todos los examenes de un curso!",
                "level": 2
            })
    if resultado_examen:
        tiempo_record = ResultadoExamen.query.filter(
            ResultadoExamen.usuario_email == email,
            ResultadoExamen.tiempo_total >= 20000).first()
        if tiempo_record:
            badges.append({
                "name": "Ágil",
                "description": "Has completado una prueba en menos de 10 minutos!",
                "level": 3
            })
    percentage_text = int((len(badges)/total_badges)*100) if badges else 0
    return jsonify({
        "badges": badges,
        "total_badges": len(badges),
        "percentage_badge_score": len(badges)/total_badges if badges else 0,
        "percentage_text": f"{percentage_text}%"
    })


@app.route('/progress_chart_data', methods=['GET'])
def progress_chart_data():
    email = request.args.get('userEmail')
    result_exams = ResultadoExamen.query.filter_by(usuario_email=email).all()
    chart_data_points = []
    chart_data_labels = []
    for result_exam in result_exams:
        chart_data_points.append(result_exam.puntaje)
        chart_data_labels.append(result_exam.examen.titulo[:10])
    if not chart_data_labels:
        chart_data_labels = [""]
        chart_data_points = [0]
    return jsonify({
        "chart_data_points": chart_data_points,
        "chart_data_labels": chart_data_labels
    })


def get_points(email: str):
    result_exams = ResultadoExamen.query.filter_by(usuario_email=email).all()
    total_points_exam = sum(exam_point.puntaje for exam_point in result_exams)
    result_extra_points = PuntajeUsuarioExtraArticulos.query.filter_by(usuario_email=email).all()
    total_points_extra_points = sum(extra_point.puntaje for extra_point in result_extra_points)
    return int(total_points_exam + total_points_extra_points)


@app.route('/total_points', methods=['GET'])
def total_points():
    """
    Cantidad de puntos por Exmanen + Puntos extras por leer los articulos
    """
    email = request.args.get('userEmail')
    return jsonify({
        "total_points": get_points(email=email),
    })


@app.route('/user_points', methods=['GET'])
def user_points():
    """
    Cantidad de puntos por Exmanen + Puntos extras por leer los articulos
    """
    user_points_list = []
    emails = db.session.query(ResultadoExamen.usuario_email).distinct().all()

    # examenes_curso = db.session.query(Examen.id).join(Articulo).filter(
    #     Articulo.curso_id == curso_id
    # ).all()
    # examenes_curso_ids = {examen.id for examen in examenes_curso}
    #
    # # Obtener todos los exámenes realizados por el usuario
    # examenes_usuario = db.session.query(ResultadoExamen.examen_id).filter_by(
    #     usuario_email=email_usuario
    # ).all()
    # examenes_usuario_ids = {examen.examen_id for examen in examenes_usuario}
    #
    # # Verificar si todos los exámenes del curso fueron realizados por el usuario
    # todos_exámenes_realizados = examenes_curso_ids.issubset(examenes_usuario_ids)
    if emails:
        email_list = [email[0] for email in emails]
        for email in email_list:
            user_points_list.append({
                "email": email.split("@")[0],
                "total_points": get_points(email=email)
            })
    return jsonify({"users_points": user_points_list})
