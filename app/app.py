import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy


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


def create_tables():
    with app.app_context():
        db.create_all()
        print("All tables created.")


def drop_tables():
    with app.app_context():
        db.drop_all()
        print("All tables dropped.")


def insert_initial_data():
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