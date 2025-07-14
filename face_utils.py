"""
Utilidades para procesamiento de imágenes y reconocimiento facial.
"""

from os import listdir
from os.path import isfile, join, splitext
import face_recognition
from werkzeug.exceptions import BadRequest
import logging


def is_picture(filename):
    """Verifica si un archivo es una imagen válida."""
    image_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in image_extensions


def get_all_picture_files(path):
    """Obtiene todos los archivos de imagen en un directorio."""
    return [
        join(path, f) for f in listdir(path) if isfile(join(path, f)) and is_picture(f)
    ]


def remove_file_ext(filename):
    """Remueve la extensión de un archivo."""
    return splitext(filename.rsplit("/", 1)[-1])[0]


def calc_face_encoding(image):
    """Calcula la codificación facial de una imagen."""
    loaded_image = face_recognition.load_image_file(image)
    faces = face_recognition.face_encodings(loaded_image)
    if len(faces) > 1:
        raise Exception("Found more than one face in the image.")
    if not faces:
        raise Exception("No face found in the image.")
    return faces[0]


def get_faces_dict(path):
    """Obtiene un diccionario de rostros desde un directorio."""
    image_files = get_all_picture_files(path)
    return dict(
        [(remove_file_ext(image), calc_face_encoding(image)) for image in image_files]
    )


def extract_image(request):
    """Extrae la imagen de un request Flask."""
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


def detect_faces_in_image(file_stream, rostros_a_comparar, recognition_threshold):
    """Detecta y compara rostros en una imagen con rostros conocidos."""
    img = face_recognition.load_image_file(file_stream)
    uploaded_faces = face_recognition.face_encodings(img)

    logging.info(f"{len(uploaded_faces)} rostro(s) detectado(s) en imagen recibida.")

    rostros_detectados = []

    if uploaded_faces:
        for uploaded_face in uploaded_faces:
            for rostro in rostros_a_comparar:
                known_encoding = rostro["encoding"]
                match = face_recognition.compare_faces(
                    [known_encoding], uploaded_face, tolerance=recognition_threshold
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
