# Imagen base ligera con Python 3.11
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y forzar buffer directo en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar FFmpeg y librerías necesarias para audio y voz de Discord
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libopus0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación
COPY . .

# Comando por defecto para arrancar el bot
CMD ["python", "main.py"]
