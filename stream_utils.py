"""
Utilidades para procesamiento de streams de video.
"""

import cv2
import face_recognition
import threading
import time
import logging


def process_stream(stream_url):
    """
    Procesa el stream para detectar rostros cada segundo.
    
    Args:
        stream_url: URL del stream de video
    """
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        logging.error("No se pudo abrir el stream en %s", stream_url)
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Error al leer frame del stream")
            break

        try:
            # Convertir frame a formato compatible con face_recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detectar rostros en el frame
            face_locations = face_recognition.face_locations(rgb_frame)
            faces_count = len(face_locations)

            if faces_count > 0:
                logging.info(f"Detectados {faces_count} rostro(s) en el stream")

        except Exception as e:
            logging.error(f"Error procesando frame: {str(e)}")

        # Esperar 1 segundo antes de procesar el siguiente frame
        time.sleep(1)

    cap.release()


def start_stream_processing(stream_url):
    """
    Inicia el procesamiento de stream en un hilo separado.
    
    Args:
        stream_url: URL del stream de video
        
    Returns:
        threading.Thread: El hilo creado para procesar el stream
    """
    stream_thread = threading.Thread(target=process_stream, args=(stream_url,), daemon=True)
    stream_thread.start()
    return stream_thread
