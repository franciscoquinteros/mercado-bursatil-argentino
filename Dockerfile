# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
# Esto lo hacemos primero para aprovechar el cacheo de Docker si requirements.txt no cambia
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de los archivos de tu aplicación al contenedor
# Asegúrate de que main.py, server.py, utils.py estén en la misma carpeta que el Dockerfile
COPY main.py .
COPY server.py .
COPY utils.py .

# Expone el puerto en el que la aplicación va a escuchar
# FastAPI/Uvicorn por defecto usan 8000, pero 80 es estándar para web en Docker
EXPOSE 80

# Comando para ejecutar la aplicación Uvicorn
# server:app -> se refiere a la instancia 'app' dentro del módulo 'server.py'
# --host 0.0.0.0 -> hace que el servidor sea accesible desde fuera del contenedor (dentro de la red de Docker)
# --port 80 -> especifica que escuche en el puerto 80 dentro del contenedor
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]