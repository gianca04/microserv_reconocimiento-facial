# Face Recognition - Docker image

This project provides a docker image which offers a web service to recognize known faces on images. It's based on the great [ageitgey/face_recognition](https://github.com/ageitgey/face_recognition) project and just add a web service using the Python `face_recognition`-library.

<a href="https://www.buymeacoffee.com/JanLoebel" rel="Buy me a coffee!">![Foo](https://cdn.buymeacoffee.com/buttons/default-orange.png)</a>

## Get started

### Build the Docker image

Start by building the docker image with a defined name. This can take a while.

```bash
docker build -t facerec_service .
```

### Run the Docker image

Start the image and forward port 8080. Optionally bind a local directory to `/root/faces` to provide a location for predefined images which will be registered at start time.

```bash
docker run -d -p8080:8080 -v faces:/root/faces facerec_service
```

## Features

### Register known faces

Simple `POST` an image-file to the `/faces` endpoint and provide an identifier.
`curl -X POST -F "file=@person1.jpg" http://localhost:8080/faces?id=person1`

### Read registered faces

Simple `GET` the `/register` endpoint.
`curl http://localhost:8080/faces`

### Identify faces on image

Simple `POST` an image-file to the web service.
`curl -X POST -F "file=@person1.jpg" http://localhost:8080/`

## Examples

In the `examples`-directory there is currently only one example that shows how to use the Raspberry Pi-Camera module to capture an image and `POST` it to the `Face Recognition - Docker image` to check for known faces.

## Notes

I'm not a Python expert, so I'm pretty sure you can optimize the Python code further :) Please feel free to send PR's or open issues.

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

#

# watch.ps1
$containerName = "facerec_dev"
$scriptToRun = "python3 /root/app/facerec_service.py"

# Si el contenedor ya existe, lo borra
if (docker ps -a --format "{{.Names}}" | Select-String -Pattern "^$containerName$") {
    Write-Host "Eliminando contenedor existente..."
    docker stop $containerName | Out-Null
    docker rm $containerName | Out-Null
}

# Corre el contenedor con volumen montado
Write-Host "Iniciando contenedor con código local montado..."
docker run -d `
  -p 8080:8080 `
  -v "${PWD}:/root/app" `
  -v "faces:/root/faces" `
  --name $containerName `
  facerec_service `
  $scriptToRun

Write-Host "Contenedor '$containerName' iniciado en http://localhost:8080"

docker run --hostname=956977c2f53c --env=PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin --env=LANG=C.UTF-8 --env=GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568 --env=PYTHON_VERSION=3.8.20 --volume=C:\Users\granc\Documents\dev\python_proyectos\face_recognition:/root --network=bridge -p 8080:8080 --restart=no --runtime=runc -d facerec_service