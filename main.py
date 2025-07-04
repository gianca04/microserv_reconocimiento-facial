from os import listdir, remove
from os.path import isfile, join, splitext
import os
import requests
import face_recognition
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
import logging

# === Configuración inicial ===

# Cargar variables del .env
load_dotenv()

LARAVEL_API_URL = os.getenv("LARAVEL_API_URL", "http://localhost:8000")
RECOGNITION_THRESHOLD = float(os.getenv("MATCH_TOLERANCE", "0.6"))
LOG_FILE_PATH = os.getenv("LOG_FILE", "reconocimiento.log")

# Configurar logging para archivo y consola
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Handler para archivo
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setLevel(logging.INFO)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formato común
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Agregar handlers al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Inicializar app Flask
app = Flask(__name__)
CORS(app)

# === Variables ===

faces_dict = {}  # (No usado si se consulta desde Laravel)
persistent_faces = "/root/faces"

# === Utilidades ===


def is_picture(filename):
    image_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in image_extensions


def get_all_picture_files(path):
    return [
        join(path, f) for f in listdir(path) if isfile(join(path, f)) and is_picture(f)
    ]


def remove_file_ext(filename):
    return splitext(filename.rsplit("/", 1)[-1])[0]


def calc_face_encoding(image):
    loaded_image = face_recognition.load_image_file(image)
    faces = face_recognition.face_encodings(loaded_image)
    if len(faces) > 1:
        raise Exception("Found more than one face in the image.")
    if not faces:
        raise Exception("No face found in the image.")
    return faces[0]


def get_faces_dict(path):
    image_files = get_all_picture_files(path)
    return dict(
        [(remove_file_ext(image), calc_face_encoding(image)) for image in image_files]
    )


def extract_image(request):
    if "file" not in request.files:
        raise BadRequest("Missing file parameter!")
    file = request.files["file"]
    if file.filename == "":
        raise BadRequest("File is empty or invalid")
    return file


def detect_faces_only(file_stream):
    """
    Detecta únicamente si existen rostros en una imagen sin hacer comparaciones.
    
    Args:
        file_stream: Archivo de imagen (puede ser un objeto file de Flask o ruta)
    
    Returns:
        dict: {
            "faces_detected": int,     // Número de rostros encontrados
            "has_faces": bool,         // True si hay al menos un rostro
            "face_locations": list     // Coordenadas de cada rostro encontrado
        }
    
    Raises:
        Exception: Si hay error al procesar la imagen
    """
    try:
        # Cargar la imagen
        img = face_recognition.load_image_file(file_stream)
        
        # Detectar ubicaciones de rostros (más rápido que calcular encodings)
        face_locations = face_recognition.face_locations(img)
        
        # Contar rostros detectados
        faces_count = len(face_locations)
        
        logging.info(f"Detección simple: {faces_count} rostro(s) encontrado(s)")
        
        return {
            "faces_detected": faces_count,
            "has_faces": faces_count > 0,
            "face_locations": face_locations
        }
        
    except Exception as e:
        logging.error(f"Error en detección de rostros: {str(e)}")
        raise Exception(f"Error processing image: {str(e)}")


# === Llamadas a Laravel ===


def get_faces_from_laravel(matricula_id):
    url = f"{LARAVEL_API_URL}/api/biometricos/matricula/{matricula_id}"
    logging.info(f"Solicitando rostros para matrícula ID {matricula_id}")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["rostros"]


def reportar_asistencias(matricula_id, rostros_detectados, timestamp):
    url = f"{LARAVEL_API_URL}/api/asistencias/registro-masivo"
    data = {
        "matricula_id": matricula_id,
        "rostros_detectados": rostros_detectados,
        "captura": timestamp,
    }
    logging.info(f"Enviando asistencias detectadas: {data}")
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        logging.info("✔ Asistencias registradas correctamente.")
        return True
    except Exception as e:
        logging.error(f"❌ Error al registrar asistencias: {str(e)}")
        return False


# === Lógica de reconocimiento ===


def detect_faces_in_image(file_stream, rostros_a_comparar):
    img = face_recognition.load_image_file(file_stream)
    uploaded_faces = face_recognition.face_encodings(img)

    logging.info(f"{len(uploaded_faces)} rostro(s) detectado(s) en imagen recibida.")

    rostros_detectados = []

    if uploaded_faces:
        for uploaded_face in uploaded_faces:
            for rostro in rostros_a_comparar:
                known_encoding = rostro["encoding"]
                match = face_recognition.compare_faces(
                    [known_encoding], uploaded_face, tolerance=RECOGNITION_THRESHOLD
                )[0]

                if match:
                    distancia = face_recognition.face_distance(
                        [known_encoding], uploaded_face
                    )[0]
                    rostros_detectados.append(
                        {"id": rostro["id"], "dist": float(distancia)}
                    )

    logging.info(f"{len(rostros_detectados)} coincidencias encontradas.")
    return {"count": len(uploaded_faces), "faces": rostros_detectados}


# === Endpoints ===


@app.route("/", methods=["POST"])
def web_recognize():
    """
    Endpoint principal para reconocimiento facial y registro de asistencias.
    
    Método: POST
    URL: /
    
    Parámetros:
    - matricula_id (query parameter, requerido): ID de la matrícula para buscar rostros registrados
    - file (form-data, requerido): Imagen a procesar (formatos: png, jpg, jpeg, gif)
    
    Proceso:
    1. Extrae la imagen del request
    2. Obtiene los rostros registrados para la matrícula desde Laravel
    3. Detecta rostros en la imagen subida
    4. Compara con rostros conocidos usando el umbral de reconocimiento
    5. Si encuentra coincidencias, registra las asistencias en Laravel
    
    Respuesta exitosa (200):
    {
        "count": 2,                    // Número de rostros detectados en la imagen
        "faces": [                     // Lista de rostros reconocidos
            {
                "id": 123,             // ID del rostro reconocido
                "dist": 0.45           // Distancia facial (menor = mayor similitud)
            }
        ],
        "asistencia_reportada": true,  // Si se pudo registrar en Laravel
        "timestamp": "2025-07-03T10:30:00"
    }
    
    Errores:
    - 400: Archivo inválido, falta matricula_id, o imagen sin formato válido
    - 500: Error al conectar con Laravel o procesar imagen
    
    Ejemplo de uso:
    curl -X POST "http://localhost:8080/?matricula_id=456" \
         -F "file=@imagen.jpg"
    """
    file = extract_image(request)
    matricula_id = request.args.get("matricula_id")

    if not matricula_id:
        logging.error("Falta el parámetro 'matricula_id'.")
        raise BadRequest("Missing 'matricula_id' in query parameters")

    if file and is_picture(file.filename):
        logging.info(f"Inicio de proceso para matrícula {matricula_id}")
        rostros = get_faces_from_laravel(matricula_id)
        resultado = detect_faces_in_image(file, rostros)

        timestamp = datetime.now().isoformat()

        if resultado["faces"]:
            enviado = reportar_asistencias(matricula_id, resultado["faces"], timestamp)
            resultado["asistencia_reportada"] = enviado
        else:
            resultado["asistencia_reportada"] = False

        resultado["timestamp"] = timestamp
        logging.info(f"Resultado del proceso: {resultado}")
        return jsonify(resultado)

    raise BadRequest("Invalid file")


@app.route("/encoding", methods=["POST"])
def encode_face():
    """
    Endpoint para obtener la codificación facial de una imagen.
    
    Método: POST
    URL: /encoding
    
    Parámetros:
    - file (form-data, requerido): Imagen con un solo rostro (formatos: png, jpg, jpeg, gif)
    
    Proceso:
    1. Extrae la imagen del request
    2. Detecta rostros en la imagen
    3. Genera la codificación facial del rostro detectado
    4. Retorna la codificación como array numérico
    
    Respuesta exitosa (200):
    {
        "encoding": [0.123, -0.456, 0.789, ...]  // Array de 128 números (codificación facial)
    }
    
    Errores (400):
    {
        "error": "Found more than one face in the image."  // Más de un rostro
    }
    {
        "error": "No face found in the image."             // Ningún rostro detectado
    }
    {
        "error": "Invalid image"                           // Formato de imagen inválido
    }
    
    Ejemplo de uso:
    curl -X POST "http://localhost:8080/encoding" \
         -F "file=@rostro.jpg"
    
    Notas:
    - La imagen debe contener exactamente un rostro
    - La codificación resultante puede usarse para comparaciones futuras
    - El array tiene exactamente 128 elementos (estándar de face_recognition)
    """
    file = extract_image(request)
    if file and is_picture(file.filename):
        try:
            encoding = calc_face_encoding(file)
            return jsonify({"encoding": encoding.tolist()})
        except Exception as e:
            logging.error(f"Error en encoding: {str(e)}")
            return jsonify({"error": str(e)}), 400
    return jsonify({"error": "Invalid image"}), 400


@app.route("/detect", methods=["POST"])
def detect_faces():
    """
    Endpoint para detectar rostros en una imagen sin hacer comparaciones.
    
    Método: POST
    URL: /detect
    
    Parámetros:
    - file (form-data, requerido): Imagen a analizar (formatos: png, jpg, jpeg, gif)
    
    Proceso:
    1. Extrae la imagen del request
    2. Detecta la presencia de rostros
    3. Retorna el conteo y ubicaciones de rostros encontrados
    
    Respuesta exitosa (200):
    {
        "faces_detected": 3,           // Número de rostros encontrados
        "has_faces": true,             // Si hay al menos un rostro
        "face_locations": [            // Coordenadas de cada rostro (top, right, bottom, left)
            [150, 300, 250, 200],
            [400, 500, 500, 400],
            [100, 200, 200, 100]
        ]
    }
    
    Errores (400):
    {
        "error": "Invalid image"                          // Formato de imagen inválido
    }
    {
        "error": "Error processing image: <detalle>"      // Error al procesar
    }
    
    Ejemplo de uso:
    curl -X POST "http://localhost:8080/detect" \
         -F "file=@grupo.jpg"
    
    Notas:
    - Más rápido que /encoding ya que no calcula codificaciones faciales
    - Útil para validar si una imagen tiene rostros antes de procesamiento
    - Las coordenadas están en formato (top, right, bottom, left) en píxeles
    - Puede detectar múltiples rostros sin problema
    """
    file = extract_image(request)
    if file and is_picture(file.filename):
        try:
            resultado = detect_faces_only(file)
            return jsonify(resultado)
        except Exception as e:
            logging.error(f"Error en detección: {str(e)}")
            return jsonify({"error": str(e)}), 400
    return jsonify({"error": "Invalid image"}), 400


@app.route("/faces", methods=["GET", "POST", "DELETE"])
def web_faces():
    """
    Endpoint para gestionar rostros almacenados localmente (CRUD).
    
    Métodos soportados: GET, POST, DELETE
    URL: /faces
    
    === GET /faces ===
    Obtiene la lista de IDs de rostros almacenados localmente.
    
    Respuesta (200):
    ["juan", "maria", "pedro"]  // Array con IDs de rostros guardados
    
    Ejemplo:
    curl -X GET "http://localhost:8080/faces"
    
    === POST /faces?id=<rostro_id> ===
    Registra un nuevo rostro en el almacenamiento local.
    
    Parámetros:
    - id (query parameter, requerido): Identificador único para el rostro
    - file (form-data, requerido): Imagen del rostro a registrar
    
    Proceso:
    1. Guarda la imagen en /root/faces/<id>.jpg
    2. Calcula y almacena la codificación facial
    3. Actualiza el diccionario en memoria
    
    Respuesta (200):
    ["juan", "maria", "pedro", "nuevo_id"]  // Lista actualizada de rostros
    
    Errores (400):
    - Falta parámetro 'id'
    - Error al procesar la imagen (más de un rostro, ningún rostro, etc.)
    
    Ejemplo:
    curl -X POST "http://localhost:8080/faces?id=carlos" \
         -F "file=@carlos.jpg"
    
    === DELETE /faces?id=<rostro_id> ===
    Elimina un rostro del almacenamiento local.
    
    Parámetros:
    - id (query parameter, requerido): ID del rostro a eliminar
    
    Proceso:
    1. Elimina la entrada del diccionario en memoria
    2. Borra el archivo físico /root/faces/<id>.jpg
    
    Respuesta (200):
    ["juan", "maria"]  // Lista actualizada sin el rostro eliminado
    
    Errores (400):
    - Falta parámetro 'id'
    - Rostro no encontrado
    
    Ejemplo:
    curl -X DELETE "http://localhost:8080/faces?id=carlos"
    
    Notas:
    - Este endpoint maneja el almacenamiento LOCAL de rostros
    - Para uso con Laravel, usar el endpoint principal "/" que consulta rostros remotos
    - Los archivos se guardan en formato JPG independientemente del formato original
    """
    if request.method == "GET":
        return jsonify(list(faces_dict.keys()))

    file = extract_image(request)
    if "id" not in request.args:
        raise BadRequest("Missing 'id' parameter!")

    if request.method == "POST":
        app.logger.info("%s loaded", file.filename)
        file.save(f"{persistent_faces}/{request.args.get('id')}.jpg")
        try:
            new_encoding = calc_face_encoding(file)
            faces_dict.update({request.args.get("id"): new_encoding})
        except Exception as exception:
            raise BadRequest(exception)

    elif request.method == "DELETE":
        faces_dict.pop(request.args.get("id"))
        remove(f"{persistent_faces}/{request.args.get('id')}.jpg")

    return jsonify(list(faces_dict.keys()))


@app.route("/status", methods=["GET"])
def health_check():
    """
    Endpoint de verificación de estado del servicio (Health Check).
    
    Método: GET
    URL: /status
    
    Propósito:
    - Verificar que el microservicio está funcionando correctamente
    - Útil para monitoreo, load balancers y orquestadores como Docker/Kubernetes
    - No requiere parámetros ni autenticación
    
    Respuesta exitosa (200):
    {
        "status": "ok",
        "message": "Face Recognition Service is running!"
    }
    
    Ejemplo de uso:
    curl -X GET "http://localhost:8080/status"
    
    Uso típico:
    - Monitoreo de infraestructura
    - Health checks en Docker Compose
    - Verificación antes de enviar tráfico real
    - Pruebas de conectividad básica
    """
    return (
        jsonify({"status": "ok", "message": "Face RecognitioService is running!"}),
        200,
    )


# === Main ===

if __name__ == "__main__":
    logging.info("Iniciando microservicio de reconocimiento facial")
    try:
        faces_dict = get_faces_dict(persistent_faces)
    except Exception as e:
        logging.warning(f"No se pudieron cargar rostros persistentes: {e}")
        faces_dict = {}

    logging.info("Servidor iniciado en puerto 8080")
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=True)
