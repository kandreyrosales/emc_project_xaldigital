import boto3
from uuid import uuid4

# Configurar el cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('educational_data')

def insert_item(pk, sk, relation_id, entity_type, nombre, contenido=None, url_contenido=None, tipo=None, data=None):
    """ Inserta un ítem en DynamoDB con validación de parámetros obligatorios """
    item = {
        'pk': pk,
        'sk': sk,
        'relation_id': relation_id,
        'type': entity_type,
        'nombre': nombre
    }
    if contenido:
        item['contenido'] = contenido
    if url_contenido:
        item['url_contenido'] = url_contenido
    if tipo:
        item['tipo'] = tipo
    if data:
        item['data'] = data

    table.put_item(Item=item)

# Insertar Especializaciones
especializacion_cardio_id = f"especializacion#{uuid4()}"
especializacion_hematologia_id = f"especializacion#{uuid4()}"

insert_item(especializacion_cardio_id, "metadata", "N/A", "especializacion", "Cardio Neumología")
insert_item(especializacion_hematologia_id, "metadata", "N/A", "especializacion", "Hematología")

# Insertar Bloques de Cursos
hipertension_bloque_id = f"bloque_curso#{uuid4()}"
hemofilia_bloque_id = f"bloque_curso#{uuid4()}"

insert_item(hipertension_bloque_id, "metadata", especializacion_cardio_id, "bloque_curso", "Hipertensión Pulmonar",
            "Curso sobre diagnóstico y tratamiento de HTP.")

insert_item(hemofilia_bloque_id, "metadata", especializacion_hematologia_id, "bloque_curso", "Hemofilia",
            "Curso sobre diagnóstico y tratamiento de Hemofilia.")

# Insertar Cursos
curso_hipertension_id = f"curso#{uuid4()}"
curso_kovaltry_id = f"curso#{uuid4()}"
curso_jivi_id = f"curso#{uuid4()}"

insert_item(curso_hipertension_id, "metadata", hipertension_bloque_id, "curso", "Hipertensión Pulmonar", "Curso inicial")
insert_item(curso_kovaltry_id, "metadata", hemofilia_bloque_id, "curso", "KOVALTRY (OCTOCOG ALFA)", "Curso inicial")
insert_item(curso_jivi_id, "metadata", hemofilia_bloque_id, "curso", "JIVI (DAMOCTOCOG ALFA PEGOL)", "Curso intermedio")

# Insertar Artículos
articulo_kovaltry_id = f"articulo#{uuid4()}"
articulo_jivi_id = f"articulo#{uuid4()}"

insert_item(articulo_kovaltry_id, "metadata", curso_kovaltry_id, "articulo", "Factor VIII q3 Tarjetón Farmacocinética",
            "PDF sobre Factor VIII q3 tarjeton farmacocinética",
            "https://archivosemc.s3.amazonaws.com/FactorVIII+Q3+Tarjeton+Farmacocinetica_HIGH.pdf", "pdf")

insert_item(articulo_jivi_id, "metadata", curso_jivi_id, "articulo", "Recombinant factor VIII with an extended half-life",
            "PDF sobre la farmacocinética extendida del Factor VIII",
            "https://archivosemc.s3.amazonaws.com/2.+JIVI%C2%AE+%5Bfactor+antihemofi%CC%81lico+(recombinante)%2C+PEGilado-aucl%5D+polvo+liofilizado.pdf", "pdf")

# Insertar Exámenes
examen_kovaltry_id = f"examen#{uuid4()}"
examen_jivi_id = f"examen#{uuid4()}"

insert_item(examen_kovaltry_id, "metadata", articulo_kovaltry_id, "examen", "Examen Factor VIII q3 Tarjetón Farmacocinética")
insert_item(examen_jivi_id, "metadata", articulo_jivi_id, "examen", "Examen Recombinant Factor VIII")

# Insertar Preguntas
preguntas_kovaltry = [
    {
        "enunciado": "¿Cuál es la principal ventaja de Kovaltry® sobre Advate® en términos de vida media de FVIII?",
        "opciones": ["Reduce la vida media en un 23%", "Prolonga la vida media en un 23%", "No afecta la vida media"],
        "respuesta_correcta": "Prolonga la vida media en un 23%"
    },
    {
        "enunciado": "¿Cuánto incrementa Kovaltry® la mediana del tiempo de actividad de FVIII >1 U/dl respecto de Advate®?",
        "opciones": ["10-12 horas", "18-20 horas", "25-30 horas"],
        "respuesta_correcta": "18-20 horas"
    }
]

preguntas_jivi = [
    {
        "enunciado": "¿Cuál ha sido uno de los principales beneficios del Factor VIII de nueva generación?",
        "opciones": ["Eliminó la necesidad de tratamiento", "Mejoró la calidad de vida", "Redució infecciones"],
        "respuesta_correcta": "Mejoró la calidad de vida"
    },
    {
        "enunciado": "¿Qué estrategia se menciona para extender la vida media del FVIII terapéutico?",
        "opciones": ["Acoplamiento a IgG", "Aumentar frecuencia de dosificación", "Usar sangre total"],
        "respuesta_correcta": "Acoplamiento a IgG"
    }
]

# Insertar preguntas en DynamoDB
for pregunta in preguntas_kovaltry:
    insert_item(f"pregunta#{uuid4()}", "metadata", examen_kovaltry_id, "pregunta", pregunta["enunciado"], data=pregunta)

for pregunta in preguntas_jivi:
    insert_item(f"pregunta#{uuid4()}", "metadata", examen_jivi_id, "pregunta", pregunta["enunciado"], data=pregunta)

# # Insertar resultados de exámenes simulados
# insert_item(f"resultado#{uuid4()}", "metadata", examen_kovaltry_id, "resultado_examen", "Resultado usuario 1",
#             data={"usuario_email": "user@example.com", "puntaje": 80, "fecha_realizacion": "2025-02-26"})
#
# insert_item(f"resultado#{uuid4()}", "metadata", examen_jivi_id, "resultado_examen", "Resultado usuario 2",
#             data={"usuario_email": "user2@example.com", "puntaje": 90, "fecha_realizacion": "2025-02-26"})

print("✅ Datos insertados exitosamente en DynamoDB.")