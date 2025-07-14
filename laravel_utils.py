"""
Utilidades para comunicación con Laravel API.
"""
import requests
import logging

def get_faces_from_laravel(matricula_id, laravel_api_url):
    """Obtiene los rostros registrados para una matrícula desde Laravel."""
    url = f"{laravel_api_url}/api/biometricos/matricula/{matricula_id}"
    logging.info(f"Solicitando rostros para matrícula ID {matricula_id}")
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["rostros"]


def reportar_asistencias(matricula_id, rostros_detectados, timestamp, laravel_api_url):
    """Reporta las asistencias detectadas a Laravel."""
    url = f"{laravel_api_url}/api/asistencias/registro-masivo"
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


def get_camaras_activas(laravel_api_url):
    """
    Obtiene la lista de cámaras activas desde Laravel.
    
    Args:
        laravel_api_url: URL base del API de Laravel
        
    Returns:
        List[Dict]: Lista de cámaras activas con sus datos
        
    Response format:
    {
        "success": true,
        "data": [
            {
                "id": 3,
                "url_stream": "http://192.168.1.7:81/stream",
                "matricula_id": 2,
                "matricula": {
                    "id": 2,
                    "codigo_matricula": "20256A",
                    "anio_escolar": "2025",
                    "grado": "Sexto",
                    "seccion": "A"
                },
                "activo": true,
                "created_at": "2025-07-14T05:03:53.000000Z",
                "updated_at": "2025-07-14T05:03:53.000000Z"
            }
        ],
        "total": 1
    }
    """
    url = f"{laravel_api_url}/api/camaras/activas"
    logging.info("Solicitando cámaras activas desde Laravel")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("success", False):
            camaras = data.get("data", [])
            logging.info(f"✅ {len(camaras)} cámara(s) activa(s) obtenida(s) desde Laravel")
            return camaras
        else:
            logging.error("❌ Respuesta de Laravel indica fallo")
            return []
            
    except requests.exceptions.Timeout:
        logging.error("❌ Timeout al obtener cámaras activas desde Laravel")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("❌ Error de conexión al obtener cámaras activas desde Laravel")
        return []
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Error HTTP al obtener cámaras activas: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"❌ Error inesperado al obtener cámaras activas: {str(e)}")
        return []
