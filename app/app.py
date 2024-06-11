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
    titulo = db.Column(db.String(100), nullable=False)
    contenido = db.Column(db.Text)
    tipo = db.Column(db.String(50), nullable=False)
    url_contenido = db.Column(db.String(200))
    curso_id = db.Column(db.Integer, db.ForeignKey('curso.id', ondelete='CASCADE'))
    curso = db.relationship('Curso', backref=db.backref('articulos', lazy=True))

    __table_args__ = (
        db.CheckConstraint(tipo.in_(['video', 'pdf']), name='check_tipo_valido'),
    )


class Examen(db.Model):
    __tablename__ = 'examen'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    articulo_id = db.Column(db.Integer, db.ForeignKey('articulo.id', ondelete='CASCADE'))
    articulo = db.relationship('Articulo', backref=db.backref('examenes', lazy=True))


class Pregunta(db.Model):
    __tablename__ = 'pregunta'
    id = db.Column(db.Integer, primary_key=True)
    enunciado = db.Column(db.String(255), nullable=False)
    opcion_a = db.Column(db.String(100), nullable=False)
    opcion_b = db.Column(db.String(100), nullable=False)
    opcion_c = db.Column(db.String(100), nullable=False)
    opcion_d = db.Column(db.String(100), nullable=False)
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


class PuntajeUsuarioExtra(db.Model):
    """
    Este modelo sirve para guardar puntaje cuando el usuario lea un PDF o termine un video, etc.
    """
    __tablename__ = 'puntaje_usuario'
    id = db.Column(db.Integer, primary_key=True)
    usuario_email = db.Column(db.String(255), nullable=False)
    puntaje_acual = db.Column(db.Float, nullable=False)


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
        especializacion = Especializacion(nombre='Cardio Neumología')
        especializacion_2 = Especializacion(nombre='Especializacion 2')
        especializacion_3 = Especializacion(nombre='Especializacion 3')
        db.session.add(especializacion)
        db.session.add(especializacion_2)
        db.session.add(especializacion_3)
        b1 = BloqueCurso(nombre="Hipertensión Pulmonar", especializacion=especializacion,
                         contenido="Este curso intensivo le brinda una comprensión profunda de la HTP, "
                                   "una condición compleja que afecta los pulmones. Explore las causas, "
                                   "la clasificación, el diagnóstico y las opciones de tratamiento, "
                                   "incluyendo medicamentos, procedimientos quirúrgicos y cuidados de apoyo.")
        b11 = BloqueCurso(nombre="Comprenda a fondo la HTP", especializacion=especializacion,
                          contenido="Mejore su comprensión de esta condición compleja para brindar "
                                    "una atención informada a los pacientes.")
        b2 = BloqueCurso(nombre="Columna", especializacion=especializacion_2)
        db.session.add(b1)
        db.session.add(b11)
        db.session.add(b2)

        curso1 = Curso(nombre="Tratamiento HTPEC", bloque_curso=b1, contenido="Este curso es inicial")
        curso2 = Curso(nombre="Tratamiento HP", bloque_curso=b1, contenido="Este curso es intermedio")
        curso3 = Curso(nombre="Diagnóstico", bloque_curso=b1, contenido="Este curso es avanzado")
        curso4 = Curso(nombre="Criptografía", bloque_curso=b2, contenido="Este curso es inicial")

        db.session.add(curso1)
        db.session.add(curso2)
        db.session.add(curso3)
        db.session.add(curso4)

        article1 = Articulo(
            titulo='Articulo tratamiento',
            contenido='Este material trata de un video muy importante',
            tipo='video',
            url_contenido='https://www.youtube.com/watch?v=qbZ-ye4xoJI&ab_channel=SPCyCCdeCardiolog%C3%ADayCirug%C3%ADaCardiovascular',
            curso=curso1
        )
        article2 = Articulo(
            titulo='Articulo tratamiento',
            contenido='Este material trata de un archivo PDF muy importante',
            tipo='pdf',
            url_contenido='https://adm.meducatium.com.ar/contenido/articulos/19502270238_1419/pdf/19502270238.pdf',
            curso=curso1
        )
        db.session.add(article1)
        db.session.add(article2)
        db.session.commit()

        data_example_article_2 = {
            "titulo": "Examen de Prueba",
            "preguntas": [
                {
                    "enunciado": "¿Cuál es la capital de Francia?",
                    "opcion_a": "Madrid",
                    "opcion_b": "París",
                    "opcion_c": "Berlín",
                    "opcion_d": "Lisboa",
                    "respuesta_correcta": "B",
                    "explicacion": "Es la respuesta porque si"
                },
                {
                    "enunciado": "¿Cuál es el resultado de 200+2?",
                    "opcion_a": "202",
                    "opcion_b": "65000",
                    "opcion_c": "5777777",
                    "opcion_d": "6222222222",
                    "respuesta_correcta": "A",
                    "explicacion": "Es la respuesta porque si y así es"
                }
            ]
        }

        data_example_article_1 = {
            "titulo": "Examen Articulo 2",
            "preguntas": [
                {
                    "enunciado": "Ejemplo de enunciado 1",
                    "opcion_a": "AAAAAAAAAAAA"*4,
                    "opcion_b": "BBBBBBBBBBBB"*4,
                    "opcion_c": "CCCCCCCCCCCC"*4,
                    "opcion_d": "DDDDDDDDDDDD"*4,
                    "respuesta_correcta": "B",
                    "explicacion": "Es la respuesta porque si"
                },
                {
                    "enunciado": "Ejemplo de enunciado 1",
                    "opcion_a": "DDDDDDDDDDD" * 4,
                    "opcion_b": "FFFFFFFF" * 4,
                    "opcion_c": "NNNNNNNNN" * 4,
                    "opcion_d": "TTTTTTTTT" * 4,
                    "respuesta_correcta": "C",
                    "explicacion": "Es la respuesta porque si"
                },
            ]
        }

        crear_examen(article2.id, data_example_article_2)
        crear_examen(article1.id, data_example_article_1)


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


@app.route('/list_blocks', methods=['GET'])
def list_blocks():
    especializacion_nombre = request.args.get('especializacion_nombre')
    especializacion_query = get_especialty(especializacion_nombre=especializacion_nombre)
    bloques_json = []
    if especializacion_query:
        for bloque in especializacion_query.bloques_curso:
            bloques_json.append({
                "nombre": bloque.nombre,
                "id": bloque.id,
                "contenido": bloque.contenido
            })
    return jsonify(bloques_json)


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
            self.results_id = last_exam_result.id
        else:
            resultado = ResultadoExamen(
                usuario_email=self.user_email,
                examen_id=self.exam.id,
                tiempo_total=self.elapsed_time,
                puntaje=self.final_score,
                respuestas=self.exam_result
            )
            self.results_id = resultado.id
            db.session.add(resultado)
        db.session.commit()

    def validate_questions(self):
        question_dict = {}
        valid_answers = 0
        invalid_answers = 0
        total_questions = len(self.questions)
        for question in self.questions:
            question_id = question.get('questionId')
            question_obj = Pregunta.query.get_or_404(question_id)
            user_option_selected = question.get('optionSelectedValue')
            if user_option_selected == question_obj.respuesta_correcta:
                valid_answers += 1
                question_dict[question_obj.id] = {
                    'enunciado_pregunta': question_obj.enunciado,
                    'respuesta_correcta': question_obj.respuesta_correcta,
                    'respuesta': 'correcta'
                }
            else:
                invalid_answers += 1
                question_dict[question_obj.id] = {
                    'enunciado_pregunta': question_obj.enunciado,
                    'respuesta_correcta': check_correct_answer(question_id=question_id),
                    'respuesta': 'incorrecta'
                }
        return {
            'questions': question_dict,
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
