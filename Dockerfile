# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia solo los archivos de dependencias primero (mejor cacheo)
COPY requirements.txt .

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de tu proyecto al contenedor (incluye prisma/)
COPY . .

# Ejecuta prisma generate solo durante la construcción
RUN prisma generate

ENV PYTHONPATH=/app

# Comando por defecto (se puede sobrescribir desde docker-compose)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
