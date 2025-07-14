#!/usr/bin/env python3
"""
Script de prueba para el sistema de salones con auto-configuración.
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:8080"

def test_health_check():
    """Prueba el health check del servicio."""
    print("🏥 Probando health check...")
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            print("✅ Servicio funcionando correctamente")
            return True
        else:
            print(f"❌ Error en health check: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servicio: {str(e)}")
        return False

def test_estado_sistema():
    """Prueba el estado general del sistema."""
    print("� Verificando estado del sistema...")
    
    try:
        response = requests.get(f"{BASE_URL}/sistema/estado")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Estado del sistema:")
            print(f"   - Auto-sync activo: {result.get('auto_sync_activo', 'N/A')}")
            print(f"   - Salones totales: {result.get('salones_totales', 'N/A')}")
            print(f"   - Salones monitoreando: {result.get('salones_monitoreando', 'N/A')}")
            print(f"   - Versión: {result.get('version', 'N/A')}")
            return result
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error en request: {str(e)}")
        return None

def test_sincronizacion_manual():
    """Prueba la sincronización manual con Laravel."""
    print("🔄 Probando sincronización manual...")
    
    try:
        response = requests.post(f"{BASE_URL}/sistema/sincronizar")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Sincronización exitosa:")
            print(f"   - Salones activos: {result.get('salones_activos', [])}")
            print(f"   - Total: {result.get('total', 0)}")
            if 'cambios' in result:
                cambios = result['cambios']
                print(f"   - Nuevos: {cambios.get('nuevos', [])}")
                print(f"   - Eliminados: {cambios.get('eliminados', [])}")
            return True
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Error en sincronización: {response.status_code}")
            print(f"   Detalles: {error_data}")
            return False
    except Exception as e:
        print(f"❌ Error en request: {str(e)}")
        return False

def test_listar_salones_auto():
    """Prueba listar salones auto-configurados."""
    print("📋 Listando salones auto-configurados...")
    
    try:
        response = requests.get(f"{BASE_URL}/salones")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Salones auto-configurados:")
            print(f"   - Total: {result.get('total', 0)}")
            print(f"   - Auto-configurado: {result.get('auto_configurado', False)}")
            print(f"   - Mensaje: {result.get('mensaje', 'N/A')}")
            
            salones = result.get('salones_activos', [])
            for salon in salones:
                if isinstance(salon, dict):
                    print(f"   - {salon.get('codigo_matricula', 'N/A')} (ID: {salon.get('matricula_id', 'N/A')}) - Monitoreando: {salon.get('monitoreando', False)}")
                else:
                    print(f"   - ID: {salon}")
            
            return salones
        else:
            print(f"❌ Error listando salones: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error en request: {str(e)}")
        return []

def test_estado_salon_especifico(matricula_id):
    """Prueba obtener el estado de un salón específico."""
    print(f"📊 Obteniendo estado del salón {matricula_id}...")
    
    try:
        response = requests.get(f"{BASE_URL}/salones/{matricula_id}/estado")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Estado del salón {matricula_id}:")
            print(f"   - Código: {result.get('codigo_matricula', 'N/A')}")
            print(f"   - Stream URL: {result.get('stream_url', 'N/A')}")
            print(f"   - Rostros cargados: {result.get('rostros_cargados', 'N/A')}")
            print(f"   - Monitoreando: {result.get('monitoreando', 'N/A')}")
            print(f"   - Detecciones hoy: {result.get('detecciones_hoy', 'N/A')}")
            print(f"   - Último cache: {result.get('ultimo_cache', 'N/A')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️ Salón {matricula_id} no encontrado")
            return False
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en request: {str(e)}")
        return False

def test_refrescar_salon(matricula_id):
    """Prueba refrescar rostros de un salón."""
    print(f"🔄 Refrescando rostros del salón {matricula_id}...")
    
    try:
        response = requests.post(f"{BASE_URL}/salones/{matricula_id}/refrescar")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Rostros refrescados: {result.get('message', 'N/A')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️ Salón {matricula_id} no encontrado para refrescar")
            return False
        else:
            print(f"❌ Error refrescando: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error en request: {str(e)}")
        return False

def test_conexion_laravel():
    """Prueba la conectividad con Laravel (informativo)."""
    print("� Probando conectividad con Laravel...")
    
    # Nota: Necesitaríamos la URL de Laravel configurada para hacer esta prueba
    # Por ahora solo es informativo
    print("⚠️ Para probar Laravel directamente, ejecuta:")
    print("   curl http://tu-laravel.com/api/camaras/activas")
    print("   curl http://tu-laravel.com/api/biometricos/matricula/2")
    return True

def main():
    """Ejecuta todas las pruebas del sistema auto-configurado."""
    print("🧪 Iniciando pruebas del sistema de salones AUTO-CONFIGURADO")
    print("=" * 60)
    
    # 1. Health check
    if not test_health_check():
        print("❌ El servicio no está funcionando. Verifica que esté ejecutándose.")
        return
    
    print()
    
    # 2. Estado general del sistema
    estado_inicial = test_estado_sistema()
    print()
    
    # 3. Información sobre Laravel
    test_conexion_laravel()
    print()
    
    # 4. Probar sincronización manual
    print("🔄 Probando sincronización con Laravel...")
    exito_sync = test_sincronizacion_manual()
    print()
    
    if not exito_sync:
        print("⚠️ La sincronización falló. Posibles causas:")
        print("   - Laravel no está accesible")
        print("   - Endpoint /api/camaras/activas no existe")
        print("   - URL incorrecta en .env (LARAVEL_API_URL)")
        print("   - No hay cámaras activas en Laravel")
        print()
    
    # 5. Listar salones auto-configurados
    salones = test_listar_salones_auto()
    print()
    
    # 6. Si hay salones, probar funcionalidades específicas
    if salones and len(salones) > 0:
        # Obtener el primer salón para pruebas
        primer_salon = salones[0]
        if isinstance(primer_salon, dict):
            matricula_id = primer_salon.get('matricula_id')
        else:
            matricula_id = primer_salon
        
        if matricula_id:
            print(f"🔍 Probando funcionalidades específicas con salón {matricula_id}...")
            
            # Estado detallado
            test_estado_salon_especifico(matricula_id)
            print()
            
            # Refrescar rostros
            test_refrescar_salon(matricula_id)
            print()
    else:
        print("⚠️ No hay salones auto-configurados para probar.")
        print("   Asegúrate de:")
        print("   - Tener cámaras activas en Laravel")
        print("   - Laravel accesible desde el microservicio")
        print("   - Endpoint /api/camaras/activas funcionando")
        print()
    
    # 7. Estado final del sistema
    print("📊 Estado final del sistema:")
    estado_final = test_estado_sistema()
    
    print()
    print("=" * 60)
    print("🎯 Resumen de pruebas:")
    
    if estado_inicial and estado_final:
        print(f"   - Auto-sync activo: {estado_final.get('auto_sync_activo', False)}")
        print(f"   - Salones detectados: {estado_final.get('salones_totales', 0)}")
        print(f"   - Salones monitoreando: {estado_final.get('salones_monitoreando', 0)}")
    
    if exito_sync and salones and len(salones) > 0:
        print("✅ Sistema funcionando correctamente con auto-configuración")
    elif exito_sync:
        print("⚠️ Sistema funciona pero no hay salones configurados en Laravel")
    else:
        print("❌ Problemas de conectividad con Laravel")
    
    print("\n📚 Para más información:")
    print("   - Ver logs: tail -f reconocimiento.log")
    print("   - Estado del sistema: curl http://localhost:8080/sistema/estado")
    print("   - Forzar sync: curl -X POST http://localhost:8080/sistema/sincronizar")
    
    print("=" * 60)
    print("🎯 Pruebas finalizadas")

if __name__ == "__main__":
    main()
