#!/usr/bin/env python3
"""
Script de instalación y configuración del microservicio de reconocimiento facial.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_python_version():
    """Verifica la versión de Python."""
    print("🐍 Verificando versión de Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} es compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} no es compatible. Se requiere Python 3.8+")
        return False

def create_env_file():
    """Crea el archivo .env si no existe."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ Archivo .env ya existe")
        return True
    
    if env_example.exists():
        print("📝 Creando archivo .env desde .env.example...")
        try:
            env_example.replace(env_file)
            print("✅ Archivo .env creado. ¡No olvides configurarlo!")
            return True
        except Exception as e:
            print(f"❌ Error creando .env: {e}")
            return False
    else:
        print("⚠️ No se encontró .env.example. Creando .env básico...")
        try:
            with open(".env", "w") as f:
                f.write("""# Configuración del Microservicio de Reconocimiento Facial
LARAVEL_API_URL=http://localhost:8000
MATCH_TOLERANCE=0.6
LOG_FILE=reconocimiento.log
STREAM_URL=http://192.168.1.100:81/stream
""")
            print("✅ Archivo .env básico creado")
            return True
        except Exception as e:
            print(f"❌ Error creando .env: {e}")
            return False

def create_directories():
    """Crea directorios necesarios."""
    directories = ["faces", "logs"]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Directorio {directory} creado")
            except Exception as e:
                print(f"❌ Error creando directorio {directory}: {e}")
                return False
    
    return True

def install_dependencies():
    """Instala las dependencias de Python."""
    print("📦 Instalando dependencias de Python...")
    
    # Verificar si pip está disponible
    if not run_command("pip --version", "Verificando pip"):
        print("❌ pip no está disponible. Instala pip primero.")
        return False
    
    # Instalar dependencias
    if not run_command("pip install -r requirements.txt", "Instalando dependencias"):
        print("❌ Error instalando dependencias. Verifica requirements.txt")
        return False
    
    return True

def test_installation():
    """Prueba que las dependencias principales funcionen."""
    print("🧪 Probando instalación...")
    
    test_imports = [
        ("flask", "Flask"),
        ("cv2", "OpenCV"),
        ("face_recognition", "Face Recognition"),
        ("requests", "Requests"),
        ("dotenv", "Python-dotenv")
    ]
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} importado correctamente")
        except ImportError as e:
            print(f"❌ Error importando {name}: {e}")
            return False
    
    return True

def show_next_steps():
    """Muestra los siguientes pasos al usuario."""
    print("\n" + "="*50)
    print("🎉 ¡Instalación completada!")
    print("="*50)
    print("\n📋 Siguientes pasos:")
    print("\n1. 📝 Configurar .env:")
    print("   - Edita el archivo .env")
    print("   - Configura LARAVEL_API_URL con tu servidor Laravel")
    print("   - Ajusta MATCH_TOLERANCE según necesites (0.6 es un buen valor inicial)")
    
    print("\n2. 🚀 Ejecutar el microservicio:")
    print("   python main.py")
    
    print("\n3. 🧪 Probar el sistema:")
    print("   python test_salones.py")
    
    print("\n4. 📡 Registrar tu primer salón:")
    print('   curl -X POST "http://localhost:8080/salones" \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"matricula_id": "salon_101", "stream_url": "http://192.168.1.100:81/stream"}\'')
    
    print("\n5. 📊 Verificar estado:")
    print('   curl -X GET "http://localhost:8080/salones"')
    
    print("\n📚 Documentación:")
    print("   - README.md - Guía completa")
    print("   - GUIA_SALONES.md - Guía detallada de salones")
    print("   - .env.example - Ejemplo de configuración")
    
    print("\n🆘 Problemas:")
    print("   - Revisa los logs: tail -f reconocimiento.log")
    print("   - Ejecuta las pruebas: python test_salones.py")
    print("   - Verifica conectividad con Laravel y ESP32")

def main():
    """Función principal de instalación."""
    print("🔧 Instalador del Microservicio de Reconocimiento Facial")
    print("=" * 60)
    
    # 1. Verificar Python
    if not check_python_version():
        return False
    
    # 2. Crear directorios
    if not create_directories():
        return False
    
    # 3. Crear archivo .env
    if not create_env_file():
        return False
    
    # 4. Instalar dependencias
    if not install_dependencies():
        return False
    
    # 5. Probar instalación
    if not test_installation():
        print("⚠️ La instalación tiene problemas. Revisa los errores arriba.")
        return False
    
    # 6. Mostrar siguientes pasos
    show_next_steps()
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Instalación exitosa")
        sys.exit(0)
    else:
        print("\n❌ Instalación falló")
        sys.exit(1)
