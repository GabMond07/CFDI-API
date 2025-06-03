from celery import Celery
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar Celery con Redis como broker
celery = Celery(
    "web_api_fiscal",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["src.tasks"]
)

# Configuración adicional de Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

if __name__ == "__main__":
    celery.start()