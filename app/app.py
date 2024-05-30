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
    especializacion_id = db.Column(db.Integer, db.ForeignKey('especializacion.id', ondelete='CASCADE'))
    especializacion = db.relationship('Especializacion', backref=db.backref('bloques_curso', lazy=True))


class Curso(db.Model):
    __tablename__ = 'curso'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
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
        b1 = BloqueCurso(nombre="Hipertensión Pulmonar", especializacion=especializacion)
        b2 = BloqueCurso(nombre="Columna", especializacion=especializacion_2)
        db.session.add(b1)
        db.session.add(b2)

        curso1 = Curso(nombre="Tratamiento HTPEC", bloque_curso=b1)
        curso2 = Curso(nombre="Tratamiento HP", bloque_curso=b1)
        curso3 = Curso(nombre="Diagnóstico", bloque_curso=b1)
        curso4 = Curso(nombre="Criptografía", bloque_curso=b2)

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


def obtener_cursos_por_especializacion(especializacion_id: int):
    especializacion = Especializacion.query.get(especializacion_id)
    if not especializacion:
        return []

    cursos = []
    for bloque in especializacion.bloques_curso:
        cursos.extend(bloque.cursos)

    return cursos


@app.route('/list_courses', methods=['GET'])
def list_courses():
    especializacion_id = int(request.args.get('especializacion_id'))
    cursos = obtener_cursos_por_especializacion(especializacion_id)
    cursos_json = []
    for curso in cursos:
        cursos_json.append({
            'id': curso.id,
            'nombre': curso.nombre,
            'bloque': curso.bloque_curso.nombre,
            'especializacion': curso.bloque_curso.especializacion.nombre
        })
    return jsonify(cursos_json)


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