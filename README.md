# Microservicio de Reconocimiento Facial

Sistema completo de reconocimiento facial para gestión de asistencias con soporte para **múltiples salones** y **monitoreo automático de streams**.

## 🚀 Características Principales

### ✨ Sistema de Salones (Nuevo)
- **Múltiples salones simultáneos**: Cada salón tiene su propio stream ESP32
- **Monitoreo automático 24/7**: Detección continua sin intervención manual  
- **Cache inteligente**: Los rostros se actualizan automáticamente cada 30 minutos
- **Gestión centralizada**: API REST para administrar todos los salones
- **Estadísticas en tiempo real**: Conteo de detecciones por salón

### 🎯 Reconocimiento Facial Avanzado
- **Detección múltiple**: Puede detectar varios rostros simultáneamente
- **Alta precisión**: Umbral de reconocimiento configurable
- **Reporte automático**: Asistencias se envían automáticamente a Laravel

### 🔗 Integración con Laravel
- **Consulta automática**: Obtiene rostros registrados por matrícula
- **Sincronización**: Cache se actualiza automáticamente
- **Reporte de asistencias**: Envío automático de detecciones

## 📋 Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ESP32-CAM     │    │   Microservicio  │    │   Laravel API   │
│   (Salón 101)   │───▶│   Reconocimiento │◀──▶│   (Rostros +    │
└─────────────────┘    │     Facial       │    │   Asistencias)  │
                       │                  │    └─────────────────┘
┌─────────────────┐    │  ┌─────────────┐ │
│   ESP32-CAM     │───▶│  │ SalonManager│ │
│   (Salón 102)   │    │  │   - Cache   │ │
└─────────────────┘    │  │   - Monitor │ │
                       │  │   - Compare │ │
┌─────────────────┐    │  └─────────────┘ │
│   ESP32-CAM     │───▶│                  │
│   (Salón 103)   │    └──────────────────┘
└─────────────────┘
```

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <repo-url>
cd microserv_reconocimiento-facial
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tu configuración
```

### 4. Ejecutar el microservicio
```bash
python main.py
```

El servicio estará disponible en `http://localhost:8080`

## 📡 API Endpoints

### Gestión de Salones

#### Registrar un salón
```bash
POST /salones
Content-Type: application/json

{
  "matricula_id": "salon_101",
  "stream_url": "http://192.168.1.100:81/stream"
}
```

#### Listar salones activos
```bash
GET /salones

# Respuesta:
{
  "salones_activos": ["salon_101", "salon_102"],
  "total": 2
}
```

#### Estado detallado de un salón
```bash
GET /salones/salon_101/estado

# Respuesta:
{
  "matricula_id": "salon_101",
  "stream_url": "http://192.168.1.100:81/stream",
  "rostros_cargados": 25,
  "ultimo_cache": "2025-07-13T10:30:00",
  "monitoreando": true,
  "detecciones_hoy": 12,
  "ultima_deteccion": "2025-07-13T11:45:00"
}
```

#### Refrescar rostros desde Laravel
```bash
POST /salones/salon_101/refrescar
```

#### Desregistrar un salón
```bash
DELETE /salones
Content-Type: application/json

{
  "matricula_id": "salon_101"
}
```

### Endpoints Legacy (Reconocimiento Manual)

#### Reconocimiento con imagen
```bash
POST /?matricula_id=salon_101
Content-Type: multipart/form-data
file: imagen.jpg
```

#### Detectar rostros
```bash
POST /detect
Content-Type: multipart/form-data
file: imagen.jpg
```

#### Obtener codificación facial
```bash
POST /encoding
Content-Type: multipart/form-data
file: rostro.jpg
```

#### Health check
```bash
GET /status
```

## 🏗️ Configuración de ESP32

Para cada ESP32-CAM, asegúrate de que transmita correctamente:

```cpp
// El stream debe ser accesible en:
// http://IP_ESP32:81/stream

// Configuración típica:
// - Puerto 81 para stream
// - Formato MJPEG
// - Resolución recomendada: 640x480 o 800x600
```

## 📝 Guía de Uso Rápido

### 1. Configurar un salón completo

```bash
# 1. Iniciar el microservicio
python main.py

# 2. Registrar el salón (esto inicia el monitoreo automático)
curl -X POST "http://localhost:8080/salones" \
     -H "Content-Type: application/json" \
     -d '{
       "matricula_id": "1A_primaria", 
       "stream_url": "http://192.168.1.100:81/stream"
     }'

# 3. Verificar que funciona
curl -X GET "http://localhost:8080/salones/1A_primaria/estado"

# ¡Listo! El sistema ahora:
# - Monitorea el stream automáticamente
# - Detecta estudiantes en tiempo real
# - Registra asistencias en Laravel
```

### 2. Gestionar múltiples salones

```bash
# Registrar varios salones
for i in {101..105}; do
  curl -X POST "http://localhost:8080/salones" \
       -H "Content-Type: application/json" \
       -d "{
         \"matricula_id\": \"salon_$i\",
         \"stream_url\": \"http://192.168.1.$i:81/stream\"
       }"
done

# Ver todos los salones
curl -X GET "http://localhost:8080/salones"
```

## 🧪 Pruebas

Ejecutar el script de pruebas integrado:

```bash
python test_salones.py
```

Este script probará:
- Conexión al servicio
- Registro de salones
- Estados y estadísticas
- Desregistro

## 📊 Monitoreo y Logs

### Ver logs en tiempo real
```bash
tail -f reconocimiento.log
```

### Logs típicos durante operación normal
```
2025-07-13 10:30:15 [INFO] SalonManager inicializado
2025-07-13 10:30:16 [INFO] Cargando rostros para matrícula salon_101
2025-07-13 10:30:17 [INFO] ✔ 25 rostros cargados para matrícula salon_101
2025-07-13 10:30:18 [INFO] ✔ Monitoreo iniciado para matrícula salon_101
2025-07-13 10:30:45 [INFO] 👤 2 rostro(s) detectado(s) en matrícula salon_101
2025-07-13 10:30:46 [INFO] 🎯 1 rostro(s) reconocido(s) en matrícula salon_101
2025-07-13 10:30:47 [INFO] ✅ Asistencias reportadas para matrícula salon_101
```

## 🔧 Troubleshooting

### Problema: No se conecta al stream ESP32
```bash
# Verificar conectividad directa
curl -I http://192.168.1.100:81/stream

# Si no responde:
# 1. Verificar que el ESP32 esté encendido
# 2. Comprobar la red (ping 192.168.1.100)
# 3. Verificar configuración del ESP32
```

### Problema: No se cargan rostros desde Laravel
```bash
# Probar conexión directa a Laravel
curl http://tu-laravel.com/api/biometricos/matricula/salon_101

# Si falla:
# 1. Verificar LARAVEL_API_URL en .env
# 2. Comprobar que la matrícula existe en Laravel
# 3. Verificar que hay rostros registrados
```

### Problema: Salón no detecta rostros
```bash
# 1. Verificar estado del salón
curl -X GET "http://localhost:8080/salones/salon_101/estado"

# 2. Refrescar rostros manualmente
curl -X POST "http://localhost:8080/salones/salon_101/refrescar"

# 3. Ajustar umbral de reconocimiento en .env
MATCH_TOLERANCE=0.7  # Más permisivo
```

## 🔄 Migración desde Sistema Legacy

Si ya tenías el sistema anterior funcionando:

1. **Backup**: Guarda tu configuración actual
2. **Actualizar**: Actualiza el código con los nuevos archivos
3. **Configurar**: Usa los nuevos endpoints `/salones` en lugar del sistema anterior
4. **Beneficios**: Obtienes monitoreo automático y gestión de múltiples salones

El sistema legacy sigue funcionando para compatibilidad, pero se recomienda migrar al nuevo sistema de salones.

## 📝 Documentación Adicional

- [Guía Detallada de Salones](GUIA_SALONES.md)
- [Archivo de configuración ejemplo](.env.example)
- [Script de pruebas](test_salones.py)

---

**¿Necesitas ayuda?** Revisa los logs, ejecuta las pruebas, y verifica la conectividad de red y Laravel.
    "timestamp": "2025-07-03T10:30:00.123456"
}
```

**Campos de respuesta**:
- `count`: Número total de rostros detectados en la imagen
- `faces`: Array de rostros reconocidos con su ID y distancia
- `asistencia_reportada`: Boolean indicando si se registró en Laravel
- `timestamp`: Marca temporal del procesamiento

**Errores**:
- `400 Bad Request`: Archivo inválido, falta matricula_id, formato no soportado
- `500 Internal Server Error`: Error de conexión con Laravel o procesamiento

**Ejemplo de uso**:
```bash
curl -X POST "http://localhost:8080/?matricula_id=456" \
     -F "file=@imagen_grupo.jpg"
```

---

### 2. POST /encoding - Obtener Codificación Facial

**Descripción**: Genera la codificación facial de una imagen que contiene exactamente un rostro.

**URL**: `POST /encoding`

**Parámetros**:
- `file` (form-data, requerido): Imagen con un solo rostro visible

**Respuesta exitosa (200)**:
```json
{
    "encoding": [0.123, -0.456, 0.789, ..., 0.321]
}
```

**Campos de respuesta**:
- `encoding`: Array de 128 números flotantes que representan la codificación facial

**Errores (400)**:
```json
{"error": "Found more than one face in the image."}
{"error": "No face found in the image."}
{"error": "Invalid image"}
```

**Ejemplo de uso**:
```bash
curl -X POST "http://localhost:8080/encoding" \
     -F "file=@rostro_individual.jpg"
```

---

### 3. GET/POST/DELETE /faces - Gestión de Rostros Locales

**Descripción**: CRUD para gestionar rostros almacenados localmente en el servidor.

#### GET /faces - Listar Rostros

**URL**: `GET /faces`

**Respuesta (200)**:
```json
["juan", "maria", "pedro", "ana"]
```

**Ejemplo**:
```bash
curl -X GET "http://localhost:8080/faces"
```

#### POST /faces - Registrar Nuevo Rostro

**URL**: `POST /faces?id=<rostro_id>`

**Parámetros**:
- `id` (query parameter, requerido): Identificador único para el rostro
- `file` (form-data, requerido): Imagen del rostro

**Proceso**:
1. Guarda imagen en `/root/faces/<id>.jpg`
2. Calcula codificación facial
3. Almacena en memoria para comparaciones futuras

**Respuesta (200)**:
```json
["juan", "maria", "pedro", "ana", "nuevo_rostro"]
```

**Ejemplo**:
```bash
curl -X POST "http://localhost:8080/faces?id=carlos" \
     -F "file=@carlos.jpg"
```

#### DELETE /faces - Eliminar Rostro

**URL**: `DELETE /faces?id=<rostro_id>`

**Parámetros**:
- `id` (query parameter, requerido): ID del rostro a eliminar

**Proceso**:
1. Elimina del diccionario en memoria
2. Borra archivo físico del disco

**Respuesta (200)**:
```json
["juan", "maria", "pedro"]
```

**Ejemplo**:
```bash
curl -X DELETE "http://localhost:8080/faces?id=carlos"
```

---

### 4. GET /status - Health Check

**Descripción**: Verificación de estado del servicio para monitoreo.

**URL**: `GET /status`

**Respuesta (200)**:
```json
{
    "status": "ok",
    "message": "Face Recognition Service is running!"
}
```

**Ejemplo**:
```bash
curl -X GET "http://localhost:8080/status"
```

## Integración con Laravel

### APIs Consumidas

#### 1. Obtener Rostros por Matrícula
```
GET {LARAVEL_API_URL}/api/biometricos/matricula/{matricula_id}
```

**Respuesta esperada**:
```json
{
    "rostros": [
        {
            "id": 123,
            "encoding": [0.123, -0.456, ...]
        }
    ]
}
```

#### 2. Registrar Asistencias
```
POST {LARAVEL_API_URL}/api/asistencias/registro-masivo
```

**Payload enviado**:
```json
{
    "matricula_id": 456,
    "rostros_detectados": [
        {"id": 123, "dist": 0.45}
    ],
    "captura": "2025-07-03T10:30:00.123456"
}
```

## Parámetros de Configuración

### Umbral de Reconocimiento (`MATCH_TOLERANCE`)
- **Rango**: 0.0 - 1.0
- **Valor por defecto**: 0.6
- **Menor valor**: Más restrictivo (mayor precisión, menos falsos positivos)
- **Mayor valor**: Más permisivo (menor precisión, más falsos positivos)

### Formatos de Imagen Soportados
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)

## Logging

El servicio registra eventos importantes en el archivo especificado en `LOG_FILE`:

```
2025-07-03 10:30:00 [INFO] Iniciando microservicio de reconocimiento facial
2025-07-03 10:30:15 [INFO] Solicitando rostros para matrícula ID 456
2025-07-03 10:30:16 [INFO] 2 rostro(s) detectado(s) en imagen recibida
2025-07-03 10:30:16 [INFO] 1 coincidencias encontradas
2025-07-03 10:30:17 [INFO] ✔ Asistencias registradas correctamente
```

## Códigos de Estado HTTP

| Código | Descripción |
|--------|-------------|
| 200    | Operación exitosa |
| 400    | Bad Request - Parámetros inválidos o faltantes |
| 500    | Error interno del servidor |

## Ejemplos de Uso Completos

### Flujo Típico de Reconocimiento

1. **Verificar estado del servicio**:
```bash
curl -X GET "http://localhost:8080/status"
```

2. **Procesar imagen para reconocimiento**:
```bash
curl -X POST "http://localhost:8080/?matricula_id=123" \
     -F "file=@foto_clase.jpg" \
     -H "Content-Type: multipart/form-data"
```

3. **Obtener codificación de un rostro nuevo**:
```bash
curl -X POST "http://localhost:8080/encoding" \
     -F "file=@nuevo_estudiante.jpg"
```

### Gestión de Rostros Locales

```bash
# Listar rostros almacenados
curl -X GET "http://localhost:8080/faces"

# Agregar nuevo rostro
curl -X POST "http://localhost:8080/faces?id=estudiante_001" \
     -F "file=@estudiante_001.jpg"

# Eliminar rostro
curl -X DELETE "http://localhost:8080/faces?id=estudiante_001"
```

## Consideraciones de Rendimiento

- **Tiempo de procesamiento**: Varía según número de rostros en imagen y base de datos
- **Memoria**: Cada codificación facial usa ~1KB en memoria
- **Concurrencia**: Flask en modo debug no es adecuado para producción
- **Para producción**: Usar WSGI server como Gunicorn o uWSGI

## Troubleshooting

### Errores Comunes

1. **"No face found in the image"**
   - Verificar calidad de la imagen
   - Asegurar que el rostro sea visible y bien iluminado

2. **"Found more than one face in the image"** (en /encoding)
   - Usar imagen con un solo rostro visible
   - Recortar imagen si es necesario

3. **Error de conexión con Laravel**
   - Verificar `LARAVEL_API_URL` en .env
   - Confirmar que Laravel API esté ejecutándose

4. **Reconocimiento impreciso**
   - Ajustar `MATCH_TOLERANCE`
   - Verificar calidad de imágenes de referencia


# 1. Clona el repositorio en tu máquina
git clone https://github.com/JanLoebel/face_recognition.git
cd face_recognition

# 2. Construye la imagen Docker (esto se hace una sola vez)
docker build -t facerec_service .

# 3. Ejecuta el contenedor montando tu código local (modo desarrollo)
# PowerShell
docker run -d `
  -p 8080:8080 `
  -v ${PWD}:/root/app `
  -v faces:/root/faces `
  --name facerec_dev `
  facerec_service `
  python3 /root/app/facerec_service.py
# CMD
docker run -d -p 8080:8080 -v %cd%:/root/app -v faces: root/faces --name facerec_dev facerec_service python3 root/app/facerec_service.py

docker run --hostname=bcdd212cff98 --env=PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --env=LANG=C.UTF-8 --env=GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568 --env=PYTHON_VERSION=3.8.20 --volume=faces:/root/faces --volume=/run/desktop/mnt/host/c/Users/granc/Documents/dev/python_proyectos/face_recognition:/root/app --network=bridge -p 8080:8080 --restart=no --runtime=runc -d facerec_service


# 4. Verifica que el contenedor está corriendo
docker ps

# 5. Reinicia el contenedor cuando hagas cambios (usando watch.ps1)
.\watch.ps1

# 6. Accede al servicio desde tu navegador o curl
curl http://localhost:8080/faces


docker run --name=microserv_reconocimiento_facial --hostname=956977c2f53c --env=PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --env=LANG=C.UTF-8 --env=GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568 --env=PYTHON_VERSION=3.8.20 --volume=C:/Users/granc/Documents/dev/python_proyectos/microserv_reconocimiento-facial:/root --network=bridge -p 8080:8080 --restart=no --runtime=runc -d facerec_service python /root/main.py
