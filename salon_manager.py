"""
Gestión de salones, streams y rostros asociados.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import cv2
import face_recognition

from laravel_utils import get_faces_from_laravel, reportar_asistencias, get_camaras_activas


class SalonManager:
    """
    Gestiona múltiples salones, cada uno con su stream y rostros asociados.
    Ahora se auto-configura obteniendo las cámaras activas desde Laravel.
    """
    
    def __init__(self, laravel_api_url: str, recognition_threshold: float = 0.6, auto_sync_interval: int = 300):
        self.laravel_api_url = laravel_api_url
        self.recognition_threshold = recognition_threshold
        self.auto_sync_interval = auto_sync_interval  # Sincronización cada 5 minutos por defecto
        
        # Diccionario de salones activos: {matricula_id: SalonData}
        self.salones: Dict[str, 'SalonData'] = {}
        
        # Lock para operaciones thread-safe
        self.lock = threading.Lock()
        
        # Configuración de cache
        self.cache_duration = timedelta(minutes=30)  # Cache por 30 minutos
        
        # Control de sincronización automática
        self.auto_sync_active = False
        self.sync_thread: Optional[threading.Thread] = None
        self.sync_stop_event = threading.Event()
        
        logging.info("SalonManager inicializado con auto-sincronización")
    
    def iniciar_auto_sincronizacion(self):
        """
        Inicia la sincronización automática con Laravel para obtener cámaras activas.
        """
        if self.auto_sync_active:
            logging.warning("Auto-sincronización ya está activa")
            return
        
        self.auto_sync_active = True
        self.sync_stop_event.clear()
        
        self.sync_thread = threading.Thread(
            target=self._auto_sync_loop,
            daemon=True
        )
        self.sync_thread.start()
        
        logging.info("🔄 Auto-sincronización iniciada")
    
    def detener_auto_sincronizacion(self):
        """
        Detiene la sincronización automática.
        """
        if not self.auto_sync_active:
            return
        
        self.auto_sync_active = False
        self.sync_stop_event.set()
        
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=10)
        
        logging.info("🛑 Auto-sincronización detenida")
    
    def _auto_sync_loop(self):
        """
        Loop principal de sincronización automática (ejecuta en hilo separado).
        """
        logging.info(f"🔄 Iniciando sincronización automática cada {self.auto_sync_interval} segundos")
        
        # Sincronizar inmediatamente al iniciar
        self.sincronizar_con_laravel()
        
        while not self.sync_stop_event.is_set():
            # Esperar el intervalo o hasta que se detenga
            if self.sync_stop_event.wait(timeout=self.auto_sync_interval):
                break  # Se solicitó detener
            
            # Realizar sincronización
            self.sincronizar_con_laravel()
    
    def sincronizar_con_laravel(self) -> bool:
        """
        Sincroniza el estado de salones con las cámaras activas en Laravel.
        
        Returns:
            bool: True si la sincronización fue exitosa
        """
        try:
            logging.info("🔄 Sincronizando con Laravel...")
            
            # Obtener cámaras activas desde Laravel
            camaras_activas = get_camaras_activas(self.laravel_api_url)
            
            with self.lock:
                # Crear conjunto de matriculas activas en Laravel
                matriculas_laravel = set()
                
                # Procesar cada cámara activa
                for camara in camaras_activas:
                    matricula_id = str(camara["matricula_id"])
                    stream_url = camara["url_stream"]
                    codigo_matricula = camara["matricula"]["codigo_matricula"]
                    
                    matriculas_laravel.add(matricula_id)
                    
                    # Si el salón no existe, crearlo
                    if matricula_id not in self.salones:
                        logging.info(f"🆕 Nueva cámara detectada: {codigo_matricula} (ID: {matricula_id})")
                        self._crear_salon_interno(matricula_id, stream_url, codigo_matricula)
                    else:
                        # Verificar si cambió la URL del stream
                        salon_existente = self.salones[matricula_id]
                        if salon_existente.stream_url != stream_url:
                            logging.info(f"🔄 URL de stream cambió para {codigo_matricula}: {stream_url}")
                            # Detener el monitoreo actual y reiniciar con nueva URL
                            salon_existente.detener_monitoreo()
                            salon_existente.stream_url = stream_url
                            salon_existente.iniciar_monitoreo()
                
                # Desregistrar salones que ya no están activos en Laravel
                salones_a_eliminar = []
                for matricula_id in self.salones.keys():
                    if matricula_id not in matriculas_laravel:
                        salon = self.salones[matricula_id]
                        logging.info(f"🗑️ Cámara desactivada en Laravel: {salon.codigo_matricula} (ID: {matricula_id})")
                        salon.detener_monitoreo()
                        salones_a_eliminar.append(matricula_id)
                
                # Eliminar salones desactivados
                for matricula_id in salones_a_eliminar:
                    del self.salones[matricula_id]
            
            logging.info(f"✅ Sincronización completada. Salones activos: {len(self.salones)}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en sincronización con Laravel: {str(e)}")
            return False
    
    def _crear_salon_interno(self, matricula_id: str, stream_url: str, codigo_matricula: str) -> bool:
        """
        Crea un salón internamente (método auxiliar para sincronización).
        
        Args:
            matricula_id: ID de la matrícula
            stream_url: URL del stream
            codigo_matricula: Código legible de la matrícula
            
        Returns:
            bool: True si se creó correctamente
        """
        try:
            # Crear datos del salón
            salon_data = SalonData(
                matricula_id=matricula_id,
                stream_url=stream_url,
                laravel_api_url=self.laravel_api_url,
                recognition_threshold=self.recognition_threshold,
                codigo_matricula=codigo_matricula
            )
            
            # Cargar rostros desde Laravel
            if salon_data.cargar_rostros():
                self.salones[matricula_id] = salon_data
                # Iniciar monitoreo del stream
                salon_data.iniciar_monitoreo()
                logging.info(f"✔ Salón {codigo_matricula} (ID: {matricula_id}) auto-registrado y monitoreando")
                return True
            else:
                logging.error(f"❌ No se pudieron cargar rostros para salón {codigo_matricula} (ID: {matricula_id})")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error creando salón {codigo_matricula}: {str(e)}")
            return False
    
    def registrar_salon(self, matricula_id: str, stream_url: str, codigo_matricula: str = None) -> bool:
        """
        Registra manualmente un nuevo salón con su stream asociado.
        NOTA: Este método es para uso manual. El sistema se auto-configura con sincronizar_con_laravel().
        
        Args:
            matricula_id: ID de la matrícula (salón)
            stream_url: URL del stream ESP32 del salón
            codigo_matricula: Código legible de la matrícula (opcional)
            
        Returns:
            bool: True si se registró correctamente
        """
        with self.lock:
            if matricula_id in self.salones:
                logging.warning(f"Salón {matricula_id} ya está registrado")
                return False
            
            return self._crear_salon_interno(matricula_id, stream_url, codigo_matricula or matricula_id)
    
    def desregistrar_salon(self, matricula_id: str) -> bool:
        """
        Desregistra un salón y detiene su monitoreo.
        
        Args:
            matricula_id: ID de la matrícula (salón)
            
        Returns:
            bool: True si se desregistró correctamente
        """
        with self.lock:
            if matricula_id not in self.salones:
                logging.warning(f"Salón {matricula_id} no está registrado")
                return False
            
            # Detener monitoreo
            self.salones[matricula_id].detener_monitoreo()
            
            # Remover del diccionario
            del self.salones[matricula_id]
            
            logging.info(f"✔ Salón {matricula_id} desregistrado")
            return True
    
    def obtener_salones_activos(self) -> List[str]:
        """
        Obtiene la lista de salones activos.
        
        Returns:
            List[str]: Lista de IDs de matrícula activos
        """
        with self.lock:
            return list(self.salones.keys())
    
    def obtener_estado_salon(self, matricula_id: str) -> Optional[Dict]:
        """
        Obtiene el estado actual de un salón.
        
        Args:
            matricula_id: ID de la matrícula (salón)
            
        Returns:
            Dict: Estado del salón o None si no existe
        """
        with self.lock:
            if matricula_id not in self.salones:
                return None
            
            salon = self.salones[matricula_id]
            return {
                "matricula_id": matricula_id,
                "codigo_matricula": salon.codigo_matricula,
                "stream_url": salon.stream_url,
                "rostros_cargados": len(salon.rostros_cache),
                "ultimo_cache": salon.ultimo_cache_update.isoformat() if salon.ultimo_cache_update else None,
                "monitoreando": salon.monitoreando,
                "detecciones_hoy": salon.detecciones_hoy,
                "ultima_deteccion": salon.ultima_deteccion.isoformat() if salon.ultima_deteccion else None
            }
    
    def refrescar_rostros_salon(self, matricula_id: str) -> bool:
        """
        Refresca manualmente los rostros de un salón desde Laravel.
        
        Args:
            matricula_id: ID de la matrícula (salón)
            
        Returns:
            bool: True si se refrescaron correctamente
        """
        with self.lock:
            if matricula_id not in self.salones:
                return False
            
            return self.salones[matricula_id].cargar_rostros()


class SalonData:
    """
    Datos y lógica específica de un salón.
    """
    
    def __init__(self, matricula_id: str, stream_url: str, laravel_api_url: str, recognition_threshold: float, codigo_matricula: str = None):
        self.matricula_id = matricula_id
        self.stream_url = stream_url
        self.laravel_api_url = laravel_api_url
        self.recognition_threshold = recognition_threshold
        self.codigo_matricula = codigo_matricula or matricula_id  # Código legible de la matrícula
        
        # Cache de rostros
        self.rostros_cache: List[Dict] = []
        self.ultimo_cache_update: Optional[datetime] = None
        
        # Control de monitoreo
        self.monitoreando = False
        self.thread_monitoreo: Optional[threading.Thread] = None
        self.detener_flag = threading.Event()
        
        # Estadísticas
        self.detecciones_hoy = 0
        self.ultima_deteccion: Optional[datetime] = None
        
        logging.info(f"SalonData creado para matrícula {self.codigo_matricula} (ID: {matricula_id})")
        
        logging.info(f"SalonData creado para matrícula {matricula_id}")
    
    def cargar_rostros(self) -> bool:
        """
        Carga los rostros desde Laravel y los guarda en cache.
        
        Returns:
            bool: True si se cargaron correctamente
        """
        try:
            logging.info(f"Cargando rostros para matrícula {self.matricula_id}")
            rostros = get_faces_from_laravel(self.matricula_id, self.laravel_api_url)
            
            self.rostros_cache = rostros
            self.ultimo_cache_update = datetime.now()
            
            logging.info(f"✔ {len(rostros)} rostros cargados para matrícula {self.matricula_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error cargando rostros para matrícula {self.matricula_id}: {str(e)}")
            return False
    
    def necesita_refrescar_cache(self) -> bool:
        """
        Verifica si el cache de rostros necesita ser refrescado.
        
        Returns:
            bool: True si necesita refrescarse
        """
        if not self.ultimo_cache_update:
            return True
        
        tiempo_transcurrido = datetime.now() - self.ultimo_cache_update
        return tiempo_transcurrido > timedelta(minutes=30)
    
    def iniciar_monitoreo(self):
        """
        Inicia el monitoreo del stream en un hilo separado.
        """
        if self.monitoreando:
            logging.warning(f"Monitoreo ya activo para matrícula {self.matricula_id}")
            return
        
        self.monitoreando = True
        self.detener_flag.clear()
        
        self.thread_monitoreo = threading.Thread(
            target=self._monitorear_stream,
            daemon=True
        )
        self.thread_monitoreo.start()
        
        logging.info(f"✔ Monitoreo iniciado para matrícula {self.matricula_id}")
    
    def detener_monitoreo(self):
        """
        Detiene el monitoreo del stream.
        """
        if not self.monitoreando:
            return
        
        self.monitoreando = False
        self.detener_flag.set()
        
        if self.thread_monitoreo and self.thread_monitoreo.is_alive():
            self.thread_monitoreo.join(timeout=5)
        
        logging.info(f"✔ Monitoreo detenido para matrícula {self.matricula_id}")
    
    def _monitorear_stream(self):
        """
        Lógica principal de monitoreo del stream (ejecuta en hilo separado).
        """
        cap = cv2.VideoCapture(self.stream_url)
        
        if not cap.isOpened():
            logging.error(f"❌ No se pudo abrir stream {self.stream_url} para matrícula {self.matricula_id}")
            self.monitoreando = False
            return
        
        logging.info(f"📹 Iniciando captura de stream para matrícula {self.matricula_id}")
        
        try:
            while not self.detener_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    logging.error(f"❌ Error leyendo frame para matrícula {self.matricula_id}")
                    break
                
                # Refrescar cache si es necesario
                if self.necesita_refrescar_cache():
                    logging.info(f"🔄 Refrescando cache de rostros para matrícula {self.matricula_id}")
                    self.cargar_rostros()
                
                # Procesar frame para detectar rostros
                self._procesar_frame(frame)
                
                # Esperar 1 segundo antes del siguiente frame
                if self.detener_flag.wait(timeout=1):
                    break
                    
        except Exception as e:
            logging.error(f"❌ Error en monitoreo de matrícula {self.matricula_id}: {str(e)}")
        
        finally:
            cap.release()
            self.monitoreando = False
            logging.info(f"📹 Captura finalizada para matrícula {self.matricula_id}")
    
    def _procesar_frame(self, frame):
        """
        Procesa un frame del stream para detectar y comparar rostros.
        
        Args:
            frame: Frame de video de OpenCV
        """
        try:
            # Convertir a RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if len(face_locations) == 0:
                return  # No hay rostros, continuar
            
            logging.info(f"👤 {len(face_locations)} rostro(s) detectado(s) en matrícula {self.matricula_id}")
            
            # Calcular encodings de rostros detectados
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            rostros_reconocidos = []
            
            # Comparar con rostros conocidos
            for face_encoding in face_encodings:
                for rostro in self.rostros_cache:
                    known_encoding = rostro["encoding"]
                    match = face_recognition.compare_faces(
                        [known_encoding], 
                        face_encoding, 
                        tolerance=self.recognition_threshold
                    )[0]
                    
                    if match:
                        distancia = face_recognition.face_distance([known_encoding], face_encoding)[0]
                        rostros_reconocidos.append({
                            "id": rostro["id"],
                            "dist": float(distancia)
                        })
                        break  # Una vez encontrada una coincidencia, pasar al siguiente rostro
            
            # Si hay rostros reconocidos, reportar asistencias
            if rostros_reconocidos:
                timestamp = datetime.now().isoformat()
                self.detecciones_hoy += len(rostros_reconocidos)
                self.ultima_deteccion = datetime.now()
                
                logging.info(f"🎯 {len(rostros_reconocidos)} rostro(s) reconocido(s) en matrícula {self.matricula_id}")
                
                # Reportar a Laravel
                enviado = reportar_asistencias(
                    self.matricula_id, 
                    rostros_reconocidos, 
                    timestamp, 
                    self.laravel_api_url
                )
                
                if enviado:
                    logging.info(f"✅ Asistencias reportadas para matrícula {self.matricula_id}")
                else:
                    logging.error(f"❌ Error reportando asistencias para matrícula {self.matricula_id}")
                    
        except Exception as e:
            logging.error(f"❌ Error procesando frame para matrícula {self.matricula_id}: {str(e)}")
