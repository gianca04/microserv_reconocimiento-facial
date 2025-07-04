FROM python:3.8-slim

# =====================
# 1. Instalación del sistema
# =====================
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libboost-all-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# =====================
# 2. Instalar Dlib
# =====================
RUN git clone -b 'v19.24' --single-branch https://github.com/davisking/dlib.git /root/dlib && \
    cd /root/dlib && \
    python3 setup.py install

# =====================
# 3. Instalar librerías de Python
# =====================
RUN pip3 install --no-cache-dir \
    flask \
    flask-cors \
    face_recognition \
    requests \
    python-dotenv

# =====================
# 4. Copiar microservicio
# =====================
COPY facerec_service.py /root/facerec_service.py

# =====================
# 5. Crear carpeta persistente para rostros
# =====================
RUN mkdir -p /root/faces

# =====================
# 6. Iniciar servicio
# =====================
CMD ["python3", "/root/facerec_service.py"]
