import os
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from dotenv import load_dotenv
import logging

# Importar utilidades locales
from face_utils import (
    is_picture, 
    calc_face_encoding, 
    get_faces_dict, 
    extract_image, 
    detect_faces_only, 
    detect_faces_in_image
)
from laravel_utils import (
    get_faces_from_laravel, 
    reportar_asistencias
)
from stream_utils import (
    start_stream_processing
)
from salon_manager import SalonManager

# === Configuración inicial ===

# Cargar variables del .env
load_dotenv()

LARAVEL_API_URL = os.getenv("LARAVEL_API_URL", "http://localhost:8000")
RECOGNITION_THRESHOLD = float(os.getenv("MATCH_TOLERANCE", "0.6"))
LOG_FILE_PATH = os.getenv("LOG_FILE", "reconocimiento.log")
STREAM_URL = os.getenv("STREAM_URL", "http://<direccion_ip>:81/stream")

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

# Inicializar SalonManager
salon_manager = SalonManager(
    laravel_api_url=LARAVEL_API_URL,
    recognition_threshold=RECOGNITION_THRESHOLD
)

# Iniciar auto-sincronización con Laravel para obtener cámaras activas
salon_manager.iniciar_auto_sincronizacion()

# === Variables ===

faces_dict = {}  # (No usado si se consulta desde Laravel)
persistent_faces = "/root/faces"

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
        rostros = get_faces_from_laravel(matricula_id, LARAVEL_API_URL)
        resultado = detect_faces_in_image(file, rostros, RECOGNITION_THRESHOLD)

        timestamp = datetime.now().isoformat()

        if resultado["faces"]:
            enviado = reportar_asistencias(matricula_id, resultado["faces"], timestamp, LARAVEL_API_URL)
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
        # Importar remove aquí para evitar conflicto con imports
        from os import remove
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


@app.route("/salones", methods=["GET", "POST", "DELETE"])
def gestionar_salones():
    """
    Endpoint para gestionar salones (matrícula + stream).
    
    ⚠️ NOTA IMPORTANTE: 
    Este sistema ahora se AUTO-CONFIGURA obteniendo las cámaras activas desde Laravel.
    El registro manual sigue disponible pero se recomienda usar la auto-sincronización.
    
    Métodos soportados: GET, POST, DELETE
    URL: /salones
    
    === GET /salones ===
    Obtiene la lista de salones registrados y monitoreando.
    
    Respuesta (200):
    {
        "salones_activos": [
            {
                "matricula_id": "2",
                "codigo_matricula": "20256A",
                "monitoreando": true
            }
        ],
        "total": 1,
        "auto_configurado": true,
        "mensaje": "Salones auto-configurados desde Laravel"
    }
    
    Ejemplo:
    curl -X GET "http://localhost:8080/salones"
    
    === POST /salones ===
    Registra manualmente un nuevo salón (NO RECOMENDADO - usar auto-sync).
    
    Body JSON requerido:
    {
        "matricula_id": "salon_101",           // ID único del salón
        "stream_url": "http://192.168.1.100:81/stream",  // URL del stream ESP32
        "codigo_matricula": "20256A"          // Código legible (opcional)
    }
    
    IMPORTANTE: Los salones registrados manualmente pueden ser sobrescritos
    por la auto-sincronización si no están en Laravel.
    
    === DELETE /salones ===
    Desregistra un salón manualmente (NO RECOMENDADO - usar Laravel).
    """
    global salon_manager
    
    if request.method == "GET":
        salones_activos = salon_manager.obtener_salones_activos()
        salones_info = []
        
        for matricula_id in salones_activos:
            estado = salon_manager.obtener_estado_salon(matricula_id)
            if estado:
                salones_info.append({
                    "matricula_id": estado["matricula_id"],
                    "codigo_matricula": estado["codigo_matricula"],
                    "monitoreando": estado["monitoreando"]
                })
        
        return jsonify({
            "salones_activos": salones_info,
            "total": len(salones_info),
            "auto_configurado": salon_manager.auto_sync_active,
            "mensaje": "Salones auto-configurados desde Laravel" if salon_manager.auto_sync_active else "Configuración manual"
        })
    
    # Para POST y DELETE necesitamos JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400
    
    if request.method == "POST":
        # Validar campos requeridos
        if "matricula_id" not in data or "stream_url" not in data:
            return jsonify({"error": "Missing required fields: matricula_id, stream_url"}), 400
        
        matricula_id = data["matricula_id"]
        stream_url = data["stream_url"]
        codigo_matricula = data.get("codigo_matricula")
        
        # Advertencia sobre uso manual
        logging.warning(f"⚠️ Registro manual de salón {matricula_id}. Se recomienda usar auto-sincronización.")
        
        # Registrar salón
        if salon_manager.registrar_salon(matricula_id, stream_url, codigo_matricula):
            return jsonify({
                "success": True,
                "message": f"Salón {matricula_id} registrado manualmente",
                "matricula_id": matricula_id,
                "advertencia": "Este salón puede ser sobrescrito por auto-sincronización"
            })
        else:
            return jsonify({"error": "Error registrando salón o salón ya existe"}), 400
    
    elif request.method == "DELETE":
        # Validar campo requerido
        if "matricula_id" not in data:
            return jsonify({"error": "Missing required field: matricula_id"}), 400
        
        matricula_id = data["matricula_id"]
        
        # Advertencia sobre uso manual
        logging.warning(f"⚠️ Desregistro manual de salón {matricula_id}. Se recomienda desactivar en Laravel.")
        
        # Desregistrar salón
        if salon_manager.desregistrar_salon(matricula_id):
            return jsonify({
                "success": True,
                "message": f"Salón {matricula_id} desregistrado manualmente",
                "advertencia": "El salón puede reaparecer en la próxima sincronización si está activo en Laravel"
            })
        else:
            return jsonify({"error": "Salón no encontrado"}), 404


@app.route("/salones/<matricula_id>/estado", methods=["GET"])
def obtener_estado_salon(matricula_id):
    """
    Obtiene el estado detallado de un salón específico.
    
    Método: GET
    URL: /salones/<matricula_id>/estado
    
    Parámetros:
    - matricula_id (path parameter): ID de la matrícula del salón
    
    Respuesta exitosa (200):
    {
        "matricula_id": "salon_101",
        "stream_url": "http://192.168.1.100:81/stream",
        "rostros_cargados": 25,                    // Cantidad de rostros en cache
        "ultimo_cache": "2025-07-13T10:30:00",     // Última actualización del cache
        "monitoreando": true,                      // Si está monitoreando activamente
        "detecciones_hoy": 12,                     // Detecciones realizadas hoy
        "ultima_deteccion": "2025-07-13T11:45:00"  // Última detección exitosa
    }
    
    Error (404):
    {
        "error": "Salón no encontrado"
    }
    
    Ejemplo:
    curl -X GET "http://localhost:8080/salones/salon_101/estado"
    
    Uso típico:
    - Monitoreo del estado de un salón específico
    - Verificar si el cache de rostros está actualizado
    - Estadísticas de detecciones
    """
    global salon_manager
    
    estado = salon_manager.obtener_estado_salon(matricula_id)
    if estado:
        return jsonify(estado)
    else:
        return jsonify({"error": "Salón no encontrado"}), 404


@app.route("/salones/<matricula_id>/refrescar", methods=["POST"])
def refrescar_rostros_salon(matricula_id):
    """
    Refresca manualmente los rostros de un salón desde Laravel.
    
    Método: POST
    URL: /salones/<matricula_id>/refrescar
    
    Parámetros:
    - matricula_id (path parameter): ID de la matrícula del salón
    
    Proceso:
    1. Realiza una nueva consulta a Laravel para obtener rostros actualizados
    2. Actualiza el cache interno del salón
    3. Continúa el monitoreo con los rostros refrescados
    
    Respuesta exitosa (200):
    {
        "success": true,
        "message": "Rostros refrescados correctamente",
        "matricula_id": "salon_101"
    }
    
    Errores:
    - 404: Salón no encontrado
    - 500: Error al conectar con Laravel
    
    Ejemplo:
    curl -X POST "http://localhost:8080/salones/salon_101/refrescar"
    
    Uso típico:
    - Forzar actualización cuando se agreguen nuevos estudiantes
    - Resolver problemas de cache desactualizado
    - Sincronizar cambios inmediatos desde Laravel
    """
    global salon_manager
    
    if salon_manager.refrescar_rostros_salon(matricula_id):
        return jsonify({
            "success": True,
            "message": "Rostros refrescados correctamente",
            "matricula_id": matricula_id
        })
    else:
        return jsonify({"error": "Salón no encontrado o error refrescando"}), 404


@app.route("/sistema/sincronizar", methods=["POST"])
def sincronizar_sistema():
    """
    Fuerza una sincronización inmediata con Laravel para obtener cámaras activas.
    
    Método: POST
    URL: /sistema/sincronizar
    
    Proceso:
    1. Consulta el endpoint /api/camaras/activas en Laravel
    2. Compara con salones actuales del microservicio
    3. Registra nuevas cámaras automáticamente
    4. Desregistra cámaras que ya no están activas
    5. Actualiza URLs de stream si cambiaron
    
    Respuesta exitosa (200):
    {
        "success": true,
        "message": "Sincronización completada",
        "salones_activos": ["2", "5", "8"],
        "total": 3,
        "cambios": {
            "nuevos": ["2"],
            "eliminados": ["1"], 
            "actualizados": ["5"]
        }
    }
    
    Error (500):
    {
        "error": "Error conectando con Laravel",
        "details": "Connection timeout"
    }
    
    Ejemplo:
    curl -X POST "http://localhost:8080/sistema/sincronizar"
    
    Uso típico:
    - Después de agregar/quitar cámaras en Laravel
    - Para resolver problemas de sincronización
    - Verificación manual del estado
    
    Nota:
    La sincronización también ocurre automáticamente cada 5 minutos.
    """
    global salon_manager
    
    try:
        # Obtener estado anterior
        salones_antes = set(salon_manager.obtener_salones_activos())
        
        # Realizar sincronización
        exito = salon_manager.sincronizar_con_laravel()
        
        if exito:
            # Obtener estado posterior
            salones_despues = set(salon_manager.obtener_salones_activos())
            
            # Calcular cambios
            nuevos = salones_despues - salones_antes
            eliminados = salones_antes - salones_despues
            # Para detectar actualizados necesitaríamos más lógica, por simplicidad lo omitimos
            
            return jsonify({
                "success": True,
                "message": "Sincronización completada",
                "salones_activos": list(salones_despues),
                "total": len(salones_despues),
                "cambios": {
                    "nuevos": list(nuevos),
                    "eliminados": list(eliminados),
                    "actualizados": []  # Por implementar si es necesario
                }
            })
        else:
            return jsonify({
                "error": "Error en sincronización con Laravel"
            }), 500
            
    except Exception as e:
        logging.error(f"Error en sincronización manual: {str(e)}")
        return jsonify({
            "error": "Error interno en sincronización",
            "details": str(e)
        }), 500


@app.route("/sistema/estado", methods=["GET"])
def estado_sistema():
    """
    Obtiene el estado general del sistema de reconocimiento facial.
    
    Método: GET
    URL: /sistema/estado
    
    Respuesta (200):
    {
        "auto_sync_activo": true,
        "salones_totales": 3,
        "salones_monitoreando": 2,
        "salones": [
            {
                "matricula_id": "2",
                "codigo_matricula": "20256A",
                "stream_url": "http://192.168.1.7:81/stream",
                "rostros_cargados": 15,
                "monitoreando": true,
                "detecciones_hoy": 5
            }
        ],
        "ultima_sincronizacion": "2025-07-14T10:30:00",
        "version": "2.0.0"
    }
    
    Ejemplo:
    curl -X GET "http://localhost:8080/sistema/estado"
    
    Uso típico:
    - Dashboard de monitoreo
    - Verificación del estado general
    - Debugging y diagnóstico
    """
    global salon_manager
    
    salones_info = []
    salones_monitoreando = 0
    
    for matricula_id in salon_manager.obtener_salones_activos():
        estado = salon_manager.obtener_estado_salon(matricula_id)
        if estado:
            salones_info.append(estado)
            if estado.get("monitoreando", False):
                salones_monitoreando += 1
    
    return jsonify({
        "auto_sync_activo": salon_manager.auto_sync_active,
        "salones_totales": len(salones_info),
        "salones_monitoreando": salones_monitoreando,
        "salones": salones_info,
        "version": "2.0.0-auto-sync"
    })


# === Inicialización del Stream ===
# NOTA: Ya no se inicia un stream único aquí.
# Ahora cada salón maneja su propio stream a través del SalonManager.
# Para usar el sistema anterior de stream único, descomenta las siguientes líneas:
# stream_thread = start_stream_processing(STREAM_URL)


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
