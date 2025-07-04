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
