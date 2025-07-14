"""
Gestión de salones, streams y rostros asociados.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
import cv2
import face_recognition
from laravel_utils import get_faces_from_laravel, get_camaras_activas, reportar_asistencias

class SalonData:
    def __init__(self, matricula_id, stream_url, laravel_api_url, recognition_threshold, codigo_matricula=None):
        self.matricula_id = matricula_id
        self.stream_url = stream_url
        self.laravel_api_url = laravel_api_url
        self.recognition_threshold = recognition_threshold
        self.codigo_matricula = codigo_matricula or f"MAT_{matricula_id}"
        
        # Cache de rostros
        self.rostros_cache = []
        self.ultimo_cache_rostros = None
        
        # Estado de monitoreo
        self.monitoreando = False
        self.stream_thread = None
        self.cache_thread = None
        
        # Estadísticas
        self.detecciones_hoy = 0
        self.ultima_deteccion = None
        
        # Inicializar
        logging.info(f"🏫 DEPURACIÓN: Inicializando SalonData para matrícula {matricula_id}")
        self.cargar_rostros()
        self.iniciar_monitoreo()

    def cargar_rostros(self):
        """Carga rostros desde Laravel con logs detallados."""
        logging.info(f"🔄 DEPURACIÓN: Iniciando carga de rostros para matrícula {self.matricula_id}")
        
        try:
            # ✅ AQUÍ SE OBTIENEN LOS ROSTROS - LOG PRINCIPAL
            rostros = get_faces_from_laravel(self.matricula_id, self.laravel_api_url)
            
            if rostros:
                self.rostros_cache = rostros
                self.ultimo_cache_rostros = datetime.now()
                
                logging.info(f"✅ DEPURACIÓN: CACHE DE ROSTROS ACTUALIZADO EXITOSAMENTE")
                logging.info(f"📊 DEPURACIÓN: Matrícula {self.matricula_id} ahora tiene {len(rostros)} rostros en cache")
                logging.info(f"⏰ DEPURACIÓN: Última actualización: {self.ultimo_cache_rostros}")
                
                # Mostrar IDs de rostros cargados en cache
                if len(rostros) <= 5:  # Si son pocos, mostrar todos
                    ids_rostros = [str(r.get("id", "SIN_ID")) for r in rostros]
                    logging.info(f"🎯 DEPURACIÓN: IDs en cache: {', '.join(ids_rostros)}")
                else:  # Si son muchos, mostrar solo los primeros 5
                    ids_primeros = [str(r.get("id", "SIN_ID")) for r in rostros[:5]]
                    logging.info(f"🎯 DEPURACIÓN: Primeros 5 IDs en cache: {', '.join(ids_primeros)}... (+{len(rostros)-5} más)")
                
            else:
                logging.warning(f"⚠️ DEPURACIÓN: NO se pudieron cargar rostros para matrícula {self.matricula_id}")
                self.rostros_cache = []
                
        except Exception as e:
            logging.error(f"❌ DEPURACIÓN: ERROR CRÍTICO cargando rostros para matrícula {self.matricula_id}: {str(e)}")
            self.rostros_cache = []

    def iniciar_monitoreo(self):
        """Inicia el monitoreo del stream."""
        if self.monitoreando:
            logging.warning(f"⚠️ Salón {self.matricula_id} ya está siendo monitoreado")
            return
        
        self.monitoreando = True
        logging.info(f"🎯 DEPURACIÓN: INICIANDO MONITOREO DE STREAM para matrícula {self.matricula_id}")
        logging.info(f"📹 DEPURACIÓN: URL del stream: {self.stream_url}")
        
        # Thread para monitoreo de stream
        self.stream_thread = threading.Thread(target=self._monitorear_stream)
        self.stream_thread.daemon = True
        self.stream_thread.start()
        
        # Thread para actualización de cache cada 30 minutos
        self.cache_thread = threading.Thread(target=self._cache_thread)
        self.cache_thread.daemon = True
        self.cache_thread.start()
        
        logging.info(f"✅ DEPURACIÓN: Threads de monitoreo iniciados para matrícula {self.matricula_id}")

    def _monitorear_stream(self):
        """Monitorea el stream y detecta rostros SIN COMPARAR."""
        logging.info(f"👁️ DEPURACIÓN: INICIANDO MONITOREO ACTIVO del stream {self.stream_url}")
        
        cap = None
        frames_procesados = 0
        frames_con_rostros = 0
        
        try:
            cap = cv2.VideoCapture(self.stream_url)
            if not cap.isOpened():
                logging.error(f"❌ DEPURACIÓN: NO se pudo abrir el stream {self.stream_url}")
                return
            
            logging.info(f"📹 DEPURACIÓN: Stream abierto correctamente - {self.stream_url}")
            
            while self.monitoreando:
                ret, frame = cap.read()
                if not ret:
                    logging.error(f"❌ DEPURACIÓN: Error leyendo frame del stream {self.stream_url}")
                    time.sleep(1)
                    continue
                
                frames_procesados += 1
                
                # Procesar solo cada 10 frames para reducir carga
                if frames_procesados % 10 == 0:
                    # ✅ AQUÍ SE DETECTAN ROSTROS - LOG PRINCIPAL
                    rostros_detectados = self._detectar_rostros_solamente(frame)
                    
                    if rostros_detectados > 0:
                        frames_con_rostros += 1
                        
                        # 🎯 LOG DETALLADO DE DETECCIÓN
                        logging.info(f"👤 DEPURACIÓN: ¡ROSTRO(S) DETECTADO(S) EN STREAM!")
                        logging.info(f"📊 DEPURACIÓN: Matrícula: {self.matricula_id}")
                        logging.info(f"📊 DEPURACIÓN: Cantidad de rostros: {rostros_detectados}")
                        logging.info(f"📊 DEPURACIÓN: Frame #{frames_procesados}")
                        logging.info(f"📊 DEPURACIÓN: Frames con rostros hasta ahora: {frames_con_rostros}")
                        logging.info(f"⏰ DEPURACIÓN: Timestamp: {datetime.now()}")
                        
                        # Actualizar estadísticas
                        self.detecciones_hoy += 1
                        self.ultima_deteccion = datetime.now()
                        
                        # Pausa para evitar spam de logs
                        time.sleep(2)
                    
                    # Log periódico de estado (cada 100 frames)
                    if frames_procesados % 100 == 0:
                        logging.info(f"📈 DEPURACIÓN: Estado del stream {self.matricula_id} - Frames: {frames_procesados}, Con rostros: {frames_con_rostros}")
                
                # Pequeña pausa para no sobrecargar
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"❌ DEPURACIÓN: ERROR CRÍTICO en monitoreo de stream {self.matricula_id}: {str(e)}")
        
        finally:
            if cap:
                cap.release()
            logging.info(f"🔚 DEPURACIÓN: Monitoreo terminado para matrícula {self.matricula_id}")

    def _detectar_rostros_solamente(self, frame):
        """Detecta rostros en un frame SIN HACER COMPARACIONES."""
        try:
            # Convertir frame de BGR a RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar ubicaciones de rostros (más rápido que encodings)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            return len(face_locations)
            
        except Exception as e:
            logging.error(f"❌ DEPURACIÓN: Error detectando rostros: {str(e)}")
            return 0

    def _cache_thread(self):
        """Thread para actualizar cache de rostros cada 30 minutos."""
        logging.info(f"🔄 DEPURACIÓN: INICIANDO THREAD DE CACHE para matrícula {self.matricula_id}")
        
        while self.monitoreando:
            time.sleep(1800)  # 30 minutos
            if self.monitoreando:  # Verificar que sigue activo
                logging.info(f"🔄 DEPURACIÓN: ACTUALIZACIÓN AUTOMÁTICA DE CACHE - matrícula {self.matricula_id}")
                self.cargar_rostros()

    def detener_monitoreo(self):
        """Detiene el monitoreo del salón."""
        logging.info(f"🛑 DEPURACIÓN: DETENIENDO MONITOREO para matrícula {self.matricula_id}")
        self.monitoreando = False

    def obtener_estado(self):
        """Obtiene el estado actual del salón."""
        return {
            "matricula_id": self.matricula_id,
            "codigo_matricula": self.codigo_matricula,
            "stream_url": self.stream_url,
            "rostros_cargados": len(self.rostros_cache),
            "ultimo_cache": self.ultimo_cache_rostros.isoformat() if self.ultimo_cache_rostros else None,
            "monitoreando": self.monitoreando,
            "detecciones_hoy": self.detecciones_hoy,
            "ultima_deteccion": self.ultima_deteccion.isoformat() if self.ultima_deteccion else None
        }


class SalonManager:
    def __init__(self, laravel_api_url, recognition_threshold):
        self.laravel_api_url = laravel_api_url
        self.recognition_threshold = recognition_threshold
        self.salones = {}
        self.auto_sync_active = False
        
        logging.info(f"🏢 DEPURACIÓN: SalonManager inicializado")
        logging.info(f"🌐 DEPURACIÓN: Laravel API URL: {laravel_api_url}")
        logging.info(f"🎯 DEPURACIÓN: Umbral de reconocimiento: {recognition_threshold}")

    def iniciar_auto_sincronizacion(self):
        """Inicia la sincronización automática con Laravel."""
        if self.auto_sync_active:
            logging.warning("⚠️ Auto-sincronización ya está activa")
            return
        
        self.auto_sync_active = True
        logging.info("🔄 DEPURACIÓN: INICIANDO AUTO-SINCRONIZACIÓN CON LARAVEL")
        
        # Realizar sincronización inicial
        self.sincronizar_con_laravel()
        
        # Thread para sincronización cada 5 minutos
        sync_thread = threading.Thread(target=self._sync_worker)
        sync_thread.daemon = True
        sync_thread.start()
        
        logging.info("✅ DEPURACIÓN: Auto-sincronización iniciada correctamente")

    def _sync_worker(self):
        """Worker thread para sincronización automática."""
        while self.auto_sync_active:
            time.sleep(300)  # 5 minutos
            if self.auto_sync_active:
                logging.info("🔄 DEPURACIÓN: SINCRONIZACIÓN AUTOMÁTICA CADA 5 MINUTOS")
                self.sincronizar_con_laravel()

    def sincronizar_con_laravel(self):
        """Sincroniza salones con cámaras activas de Laravel."""
        logging.info("🔄 DEPURACIÓN: INICIANDO SINCRONIZACIÓN CON LARAVEL")
        
        try:
            # ✅ OBTENER CÁMARAS ACTIVAS
            camaras = get_camaras_activas(self.laravel_api_url)
            
            if not camaras:
                logging.warning("⚠️ DEPURACIÓN: No se obtuvieron cámaras activas de Laravel")
                return False
            
            # Procesar cada cámara
            for camara in camaras:
                matricula_id = str(camara.get("matricula_id"))
                stream_url = camara.get("url_stream")
                codigo_matricula = camara.get("matricula", {}).get("codigo_matricula", f"MAT_{matricula_id}")
                
                logging.info(f"🔄 DEPURACIÓN: Procesando cámara - Matrícula: {matricula_id}, Stream: {stream_url}")
                
                if matricula_id not in self.salones:
                    # ✅ REGISTRAR NUEVO SALÓN
                    logging.info(f"➕ DEPURACIÓN: REGISTRANDO NUEVO SALÓN - Matrícula: {matricula_id}")
                    self.registrar_salon(matricula_id, stream_url, codigo_matricula)
                else:
                    logging.info(f"✅ DEPURACIÓN: Salón ya existe - Matrícula: {matricula_id}")
            
            logging.info(f"✅ DEPURACIÓN: SINCRONIZACIÓN COMPLETADA - {len(camaras)} cámara(s) procesada(s)")
            return True
            
        except Exception as e:
            logging.error(f"❌ DEPURACIÓN: ERROR EN SINCRONIZACIÓN: {str(e)}")
            return False

    def registrar_salon(self, matricula_id, stream_url, codigo_matricula=None):
        """Registra un nuevo salón."""
        if matricula_id in self.salones:
            logging.warning(f"⚠️ DEPURACIÓN: Salón {matricula_id} ya está registrado")
            return False
        
        logging.info(f"➕ DEPURACIÓN: REGISTRANDO SALÓN - Matrícula: {matricula_id}")
        
        try:
            salon_data = SalonData(
                matricula_id=matricula_id,
                stream_url=stream_url,
                laravel_api_url=self.laravel_api_url,
                recognition_threshold=self.recognition_threshold,
                codigo_matricula=codigo_matricula
            )
            
            self.salones[matricula_id] = salon_data
            logging.info(f"✅ DEPURACIÓN: Salón {matricula_id} registrado exitosamente")
            return True
            
        except Exception as e:
            logging.error(f"❌ DEPURACIÓN: Error registrando salón {matricula_id}: {str(e)}")
            return False

    def obtener_salones_activos(self):
        """Obtiene lista de salones activos."""
        return list(self.salones.keys())

    def obtener_estado_salon(self, matricula_id):
        """Obtiene estado de un salón específico."""
        if matricula_id in self.salones:
            return self.salones[matricula_id].obtener_estado()
        return None

    def refrescar_rostros_salon(self, matricula_id):
        """Refresca rostros de un salón específico."""
        if matricula_id in self.salones:
            logging.info(f"🔄 DEPURACIÓN: REFRESCANDO ROSTROS MANUALMENTE - Matrícula: {matricula_id}")
            self.salones[matricula_id].cargar_rostros()
            return True
        return False

    def desregistrar_salon(self, matricula_id):
        """Desregistra un salón."""
        if matricula_id in self.salones:
            logging.info(f"🛑 DEPURACIÓN: DESREGISTRANDO SALÓN - Matrícula: {matricula_id}")
            self.salones[matricula_id].detener_monitoreo()
            del self.salones[matricula_id]
            return True
        return False
