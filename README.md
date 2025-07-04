# Documentación API - Microservicio de Reconocimiento Facial

## Descripción General

Este microservicio proporciona funcionalidades de reconocimiento facial utilizando la librería `face_recognition`. Está diseñado para integrarse con un sistema Laravel y permite detectar rostros en imágenes, compararlos con una base de datos de rostros conocidos, y registrar asistencias automáticamente.

## Configuración

### Variables de Entorno (.env)

```env
LARAVEL_API_URL=http://localhost:8000        # URL del backend Laravel
MATCH_TOLERANCE=0.6                          # Umbral de reconocimiento (0.0-1.0)
LOG_FILE=reconocimiento.log                  # Archivo de logs
```

### Puerto del Servicio
- **Puerto por defecto**: 8080
- **Host**: 0.0.0.0 (acepta conexiones externas)

## Endpoints

### 1. POST / - Reconocimiento Facial y Registro de Asistencias

**Descripción**: Endpoint principal que procesa una imagen, detecta rostros, los compara con rostros registrados en Laravel y registra asistencias automáticamente.

**URL**: `POST /`

**Parámetros**:
- `matricula_id` (query parameter, requerido): ID de la matrícula para obtener rostros registrados
- `file` (form-data, requerido): Imagen a procesar (PNG, JPG, JPEG, GIF)

**Flujo de procesamiento**:
1. Extrae imagen del request
2. Consulta rostros registrados en Laravel para la matrícula
3. Detecta rostros en la imagen subida
4. Compara cada rostro detectado con los rostros conocidos
5. Si encuentra coincidencias, registra asistencias en Laravel

**Respuesta exitosa (200)**:
```json
{
    "count": 2,
    "faces": [
        {
            "id": 123,
            "dist": 0.45
        },
        {
            "id": 124,
            "dist": 0.52
        }
    ],
    "asistencia_reportada": true,
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
