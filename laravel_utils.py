"""
Utilidades para comunicación con Laravel API.
"""
import requests
import logging

def get_faces_from_laravel(matricula_id, laravel_api_url):
    """Obtiene los rostros registrados para una matrícula desde Laravel."""
    url = f"{laravel_api_url}/api/biometricos/matricula/{matricula_id}"
    logging.info(f"🔍 DEPURACIÓN: Solicitando rostros para matrícula ID {matricula_id}")
    logging.info(f"🌐 DEPURACIÓN: URL consulta: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        rostros = data.get("rostros", [])
        
        # ✅ LOG DETALLADO DE ROSTROS OBTENIDOS
        logging.info(f"✅ DEPURACIÓN: ROSTROS OBTENIDOS EXITOSAMENTE para matrícula {matricula_id}")
        logging.info(f"📊 DEPURACIÓN: Total de rostros: {len(rostros)}")
        
        if rostros:
            logging.info(f"👥 DEPURACIÓN: Lista de IDs de rostros obtenidos:")
            for i, rostro in enumerate(rostros, 1):
                rostro_id = rostro.get("id", "SIN_ID")
                logging.info(f"   {i}. Rostro ID: {rostro_id}")
        else:
            logging.warning(f"⚠️ DEPURACIÓN: NO se encontraron rostros para matrícula {matricula_id}")
        
        logging.info(f"🎯 DEPURACIÓN: Rostros listos para usar en comparaciones")
        return rostros
        
    except requests.exceptions.Timeout:
        logging.error(f"❌ DEPURACIÓN: TIMEOUT obteniendo rostros para matrícula {matricula_id}")
        return []
    except requests.exceptions.ConnectionError:
        logging.error(f"❌ DEPURACIÓN: ERROR DE CONEXIÓN obteniendo rostros para matrícula {matricula_id}")
        return []
    except Exception as e:
        logging.error(f"❌ DEPURACIÓN: ERROR INESPERADO obteniendo rostros: {str(e)}")
        return []

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
    """Obtiene la lista de cámaras activas desde Laravel."""
    url = f"{laravel_api_url}/api/camaras/activas"
    logging.info("🔍 DEPURACIÓN: Consultando cámaras activas desde Laravel")
    logging.info(f"🌐 DEPURACIÓN: URL consulta: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("success", False):
            camaras = data.get("data", [])
            
            # ✅ LOG DETALLADO DE CÁMARAS OBTENIDAS
            logging.info(f"✅ DEPURACIÓN: CÁMARAS ACTIVAS OBTENIDAS EXITOSAMENTE")
            logging.info(f"📊 DEPURACIÓN: Total de cámaras activas: {len(camaras)}")
            
            if camaras:
                logging.info(f"📹 DEPURACIÓN: Lista de cámaras activas:")
                for i, camara in enumerate(camaras, 1):
                    matricula_id = camara.get("matricula_id", "SIN_MATRICULA")
                    stream_url = camara.get("url_stream", "SIN_URL")
                    codigo = camara.get("matricula", {}).get("codigo_matricula", "SIN_CODIGO")
                    logging.info(f"   {i}. Matrícula: {matricula_id} | Código: {codigo} | Stream: {stream_url}")
            else:
                logging.warning(f"⚠️ DEPURACIÓN: NO se encontraron cámaras activas")
            
            return camaras
        else:
            logging.error("❌ DEPURACIÓN: Respuesta de Laravel indica fallo")
            return []
            
    except requests.exceptions.Timeout:
        logging.error("❌ DEPURACIÓN: TIMEOUT obteniendo cámaras activas desde Laravel")
        return []
    except requests.exceptions.ConnectionError:
        logging.error("❌ DEPURACIÓN: ERROR DE CONEXIÓN obteniendo cámaras activas desde Laravel")
        return []
    except Exception as e:
        logging.error(f"❌ DEPURACIÓN: ERROR INESPERADO obteniendo cámaras activas: {str(e)}")
        return []
