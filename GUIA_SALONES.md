# Guía de Uso - Sistema de Salones con Auto-Configuración

## 🚀 Nueva Funcionalidad: Auto-Configuración

El sistema ahora se **auto-configura automáticamente** obteniendo las cámaras activas directamente desde Laravel. ¡Ya no necesitas registrar salones manualmente!

## Arquitectura del Sistema

El sistema ahora soporta **múltiples salones** donde cada salón tiene:
- **Una matrícula ID** (identificador único del salón)
- **Un stream ESP32** (cámara específica del salón) 
- **Rostros asociados** (estudiantes registrados en Laravel para esa matrícula)

### 🔄 Flujo Automático

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Laravel API   │◀───│   Microservicio  │───▶│   ESP32 Cámaras │
│                 │    │                  │    │                 │
│ /api/camaras/   │    │  Auto-sync cada  │    │ Stream continuo │
│ activas         │    │  5 minutos       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        │                       │
         ▼                        ▼                       ▼
   Configuración            Cache inteligente        Detección
   automática               de rostros               automática
```

## Flujo de Trabajo Nuevo

### 1. Configuración Inicial (Una sola vez)

```bash
# 1. Asegúrate de tener el archivo .env configurado
cp .env.example .env

# 2. Edita SOLO la URL de Laravel
LARAVEL_API_URL=http://tu-laravel-server.com
MATCH_TOLERANCE=0.6
```

### 2. ¡Ejecutar y Listo! 🎉

```bash
# 1. Iniciar el microservicio
python main.py

# 🚀 ¡YA ESTÁ! El sistema automáticamente:
# - Consulta Laravel para obtener cámaras activas
# - Registra cada cámara automáticamente  
# - Carga rostros para cada matrícula
# - Inicia monitoreo de todos los streams
# - Detecta y reporta asistencias
```

**¿Qué sucede automáticamente?**
1. 🔄 Cada 5 minutos consulta `http://laravel.com/api/camaras/activas`
2. 📝 Registra nuevas cámaras automáticamente
3. 🗑️ Desregistra cámaras que ya no están activas
4. 🔄 Actualiza URLs de stream si cambiaron
5. 📊 Mantiene estadísticas de cada salón

### 3. Verificar que Todo Funciona

```bash
# Ver estado general del sistema
curl -X GET "http://localhost:8080/sistema/estado"

# Ver salones auto-configurados
curl -X GET "http://localhost:8080/salones"

# Ver estado detallado de un salón específico  
curl -X GET "http://localhost:8080/salones/2/estado"
```

### 4. Forzar Sincronización (Opcional)

Si agregas/quitas cámaras en Laravel y no quieres esperar 5 minutos:

```bash
# Sincronizar inmediatamente
curl -X POST "http://localhost:8080/sistema/sincronizar"
```
curl -X GET "http://localhost:8080/salones"
```

### 4. Monitorear Estado de Salones

```bash
# Estado general de todos los salones
curl -X GET "http://localhost:8080/salones"

# Estado detallado de un salón específico
curl -X GET "http://localhost:8080/salones/salon_101/estado"

# Respuesta esperada:
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

### 5. Actualizar Rostros

Cuando se agregan nuevos estudiantes en Laravel:

```bash
# Refrescar rostros de un salón específico
curl -X POST "http://localhost:8080/salones/salon_101/refrescar"
```

### 6. Desregistrar un Salón

```bash
curl -X DELETE "http://localhost:8080/salones" \
     -H "Content-Type: application/json" \
     -d '{"matricula_id": "salon_101"}'
```

## Endpoints Disponibles

### 🎯 Nuevos Endpoints (Auto-Configuración)
- `GET /sistema/estado` - Estado general del sistema
- `POST /sistema/sincronizar` - Forzar sincronización con Laravel
- `GET /salones` - Ver salones auto-configurados  
- `GET /salones/{id}/estado` - Estado detallado de un salón
- `POST /salones/{id}/refrescar` - Actualizar rostros de un salón

### 📋 Configuración en Laravel

Para que funcione la auto-configuración, asegúrate de que Laravel tenga:

1. **Endpoint `/api/camaras/activas`** que retorne:
```json
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
      "activo": true
    }
  ],
  "total": 1
}
```

2. **Campos requeridos por cámara**:
   - `url_stream`: URL del stream ESP32
   - `matricula_id`: ID de la matrícula asociada
   - `matricula.codigo_matricula`: Código legible
   - `activo`: true (solo se toman las activas)

### 🔧 Endpoints Legacy (Uso Manual - No Recomendado)
- `POST /salones` - Registrar salón manualmente
- `DELETE /salones` - Desregistrar salón manualmente
- `POST /` - Reconocimiento manual con imagen
- `POST /encoding` - Obtener codificación facial
- `POST /detect` - Detectar rostros en imagen
- `GET /status` - Health check

⚠️ **Advertencia**: Los salones registrados manualmente pueden ser sobrescritos por la auto-sincronización.

## Ventajas del Nuevo Sistema

### ✅ Antes (Sistema Manual)
- Registro manual de cada salón
- Configuración individual por API
- Sin sincronización con Laravel
- Gestión descentralizada

### 🚀 Ahora (Sistema Auto-Configurado)
- **🔄 Auto-configuración completa** desde Laravel
- **📊 Sincronización automática** cada 5 minutos
- **🎯 Gestión centralizada** desde Laravel
- **🔧 Mantenimiento automático** (alta/baja de cámaras)
- **📈 Sin intervención manual** requerida
- **🛡️ Detección de cambios** automática (URLs, estados)

## Ejemplo de Flujo Completo

```bash
# 1. Configurar cámaras en Laravel (Panel Admin)
# - Crear matrícula: "20256A" 
# - Asignar cámara con IP: 192.168.1.7:81/stream
# - Marcar como "activa"

# 2. Iniciar microservicio (solo una vez)
python main.py

# 🎉 ¡LISTO! El sistema automáticamente:
# - Detecta la nueva cámara en Laravel
# - Carga rostros de la matrícula 20256A  
# - Inicia monitoreo del stream 192.168.1.7:81
# - Detecta estudiantes en tiempo real
# - Registra asistencias automáticamente

# 3. Verificar funcionamiento
curl -X GET "http://localhost:8080/sistema/estado"

# Respuesta esperada:
{
  "auto_sync_activo": true,
  "salones_totales": 1,
  "salones_monitoreando": 1,
  "salones": [
    {
      "matricula_id": "2",
      "codigo_matricula": "20256A", 
      "stream_url": "http://192.168.1.7:81/stream",
      "rostros_cargados": 15,
      "monitoreando": true,
      "detecciones_hoy": 0
    }
  ]
}

# 4. Agregar más cámaras (en Laravel)
# - El microservicio las detectará automáticamente en máximo 5 minutos
# - O forzar sincronización: curl -X POST "http://localhost:8080/sistema/sincronizar"
```

## Configuración ESP32

Para cada ESP32, asegúrate de que transmita en el formato correcto:

```cpp
// Ejemplo para ESP32-CAM
// El stream debe ser accesible en: http://IP_ESP32:81/stream
// Puerto 81 es el estándar, pero puedes cambiarlo según tu configuración
```

## Troubleshooting

### ❓ Problema: No aparecen salones auto-configurados
```bash
# 1. Verificar conectividad con Laravel
curl http://tu-laravel.com/api/camaras/activas

# 2. Verificar estado del sistema
curl -X GET "http://localhost:8080/sistema/estado"

# 3. Forzar sincronización
curl -X POST "http://localhost:8080/sistema/sincronizar"

# 4. Verificar logs
tail -f reconocimiento.log

# Causas comunes:
# - Laravel no accesible desde el microservicio
# - Endpoint /api/camaras/activas no implementado
# - No hay cámaras marcadas como "activas" en Laravel
# - URL incorrecta en .env (LARAVEL_API_URL)
```

### ❓ Problema: Salón no detecta rostros
```bash
# 1. Verificar estado del salón específico
curl -X GET "http://localhost:8080/salones/2/estado"

# 2. Refrescar rostros desde Laravel
curl -X POST "http://localhost:8080/salones/2/refrescar"

# 3. Verificar stream ESP32 directamente
curl -I http://192.168.1.7:81/stream

# 4. Verificar logs en tiempo real
tail -f reconocimiento.log

# Causas comunes:
# - ESP32 no accesible o apagado
# - No hay rostros registrados para esa matrícula en Laravel
# - Umbral de reconocimiento muy estricto (ajustar MATCH_TOLERANCE)
```

### ❓ Problema: Stream no se conecta
```bash
# 1. Probar stream directamente en navegador
http://192.168.1.7:81/stream

# 2. Verificar red (ping al ESP32)
ping 192.168.1.7

# 3. Verificar configuración ESP32
# - Puerto correcto (normalmente 81)
# - Stream MJPEG funcionando
# - ESP32 en la misma red que el microservicio
```

### ❓ Problema: No se cargan rostros desde Laravel
```bash
# 1. Probar endpoint de rostros directamente
curl http://tu-laravel.com/api/biometricos/matricula/2

# 2. Verificar que existe la matrícula en Laravel
# 3. Verificar que hay rostros registrados para esa matrícula
# 4. Verificar permisos de API en Laravel

# Causas comunes:
# - Matrícula no existe en Laravel
# - No hay estudiantes registrados con rostros
# - Endpoint /api/biometricos/matricula/{id} no funciona
# - Problemas de autenticación/autorización en Laravel
```

### 🔧 Comandos de Diagnóstico Útiles

```bash
# Estado completo del sistema
curl -X GET "http://localhost:8080/sistema/estado" | jq

# Logs en vivo con filtrado
tail -f reconocimiento.log | grep -E "(ERROR|WARNING|✅|❌)"

# Probar conectividad con Laravel  
curl -v http://tu-laravel.com/api/camaras/activas

# Ver salones activos con formato
curl -X GET "http://localhost:8080/salones" | jq

# Forzar sincronización y ver resultado
curl -X POST "http://localhost:8080/sistema/sincronizar" | jq
```
