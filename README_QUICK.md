# 🚀 Microservicio de Reconocimiento Facial v2.0 - Auto-Configuración

## ¿Qué es nuevo?

**¡El sistema ahora se AUTO-CONFIGURA completamente desde Laravel!** 🎉

Ya no necesitas registrar salones manualmente. El microservicio consulta automáticamente el endpoint `/api/camaras/activas` de Laravel y configura todo por ti.

## 🏃‍♂️ Inicio Rápido

### 1. Configurar Laravel (Una sola vez)

Asegúrate de que Laravel tenga el endpoint `/api/camaras/activas` que retorne:

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

### 2. Configurar el Microservicio (Una sola vez)

```bash
# 1. Clonar y instalar
git clone <repo>
cd microserv_reconocimiento-facial
python setup.py

# 2. Configurar .env (solo cambiar la URL de Laravel)
cp .env.example .env
# Editar: LARAVEL_API_URL=http://tu-laravel.com
```

### 3. ¡Ejecutar y Listo! 🎉

```bash
# Iniciar microservicio
python main.py

# 🚀 ¡YA ESTÁ! El sistema automáticamente:
# ✅ Detecta cámaras activas en Laravel
# ✅ Registra cada cámara automáticamente
# ✅ Carga rostros para cada matrícula
# ✅ Inicia monitoreo de todos los streams
# ✅ Detecta estudiantes en tiempo real
# ✅ Reporta asistencias automáticamente
```

## 📊 Verificar que Funciona

```bash
# Ver estado general
curl -X GET "http://localhost:8080/sistema/estado"

# Ver salones auto-configurados  
curl -X GET "http://localhost:8080/salones"

# Forzar sincronización inmediata
curl -X POST "http://localhost:8080/sistema/sincronizar"
```

## 🔧 Gestión de Cámaras

### Agregar una cámara nueva:
1. 📱 Configurar ESP32-CAM en la red
2. 🖥️ Agregar cámara en Laravel (panel admin)
3. ✅ ¡Listo! El microservicio la detectará automáticamente (máximo 5 min)

### Quitar una cámara:
1. 🖥️ Desactivar cámara en Laravel
2. ✅ ¡Listo! El microservicio dejará de monitorearla automáticamente

## 📋 Flujo Automático

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Laravel API   │◀───│   Microservicio  │───▶│   ESP32 Cámaras │
│                 │    │                  │    │                 │
│ Configura       │    │ Auto-sync cada   │    │ Stream continuo │
│ cámaras activas │    │ 5 minutos        │    │ MJPEG           │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         ▼                        ▼                       ▼
   ✅ Panel Admin          🔄 Sin intervención      📹 Detección
   ✅ Activar/Desactivar   🔄 Cache inteligente     📹 Automática
   ✅ Gestión central      🔄 Estadísticas          📹 24/7
```

## 🆘 Problemas Comunes

### No aparecen salones auto-configurados
```bash
# Verificar conectividad con Laravel
curl http://tu-laravel.com/api/camaras/activas

# Si falla, revisar:
# - URL correcta en .env
# - Laravel accesible desde microservicio
# - Endpoint implementado en Laravel
# - Hay cámaras marcadas como "activas"
```

### Salón no detecta rostros
```bash
# Verificar stream ESP32
curl -I http://192.168.1.7:81/stream

# Verificar rostros en Laravel
curl http://tu-laravel.com/api/biometricos/matricula/2

# Ajustar tolerancia en .env
MATCH_TOLERANCE=0.7  # Más permisivo
```

## 📚 Documentación Completa

- [README.md](README.md) - Documentación técnica completa
- [GUIA_SALONES.md](GUIA_SALONES.md) - Guía detallada con ejemplos
- [test_salones.py](test_salones.py) - Script de pruebas
- [setup.py](setup.py) - Instalador automático

## 🔄 Migración desde v1.0

Si ya tenías el sistema anterior:
1. 🗂️ Backup de configuración actual
2. ⬆️ Actualizar código a v2.0
3. 🖥️ Configurar cámaras en Laravel
4. 🚀 Ejecutar - ¡Todo se configura automáticamente!

## 💡 Ventajas de v2.0

| Antes (v1.0) | Ahora (v2.0) |
|---------------|--------------|
| ❌ Registro manual por API | ✅ Auto-configuración desde Laravel |
| ❌ Gestión descentralizada | ✅ Gestión centralizada en Laravel |
| ❌ Sin sincronización | ✅ Sincronización automática cada 5 min |
| ❌ Configuración compleja | ✅ Configuración de una sola vez |
| ❌ Mantenimiento manual | ✅ Mantenimiento automático |

---

**¿Dudas?** Revisa la documentación completa en [GUIA_SALONES.md](GUIA_SALONES.md) o ejecuta `python test_salones.py` para verificar el funcionamiento.
