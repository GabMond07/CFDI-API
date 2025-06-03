# CFDI-API

Comandos para ejecutar el proyecto:

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servidor
uvicorn src.main:app --reload

```

```bash

# Ejecutar pruebas
pytest
```

## Ejecución de tareas

Tareas de Celery se ejecutan en un servidor Redis. Para ejecutar tareas en segundo plano, se debe iniciar el servidor Redis y ejecutar el comando `celery -A src.celery_app worker --loglevel=info`.

```bash
# Iniciar servidor Redis
redis-server

# Ejecutar tareas en segundo plano
celery -A src.celery_app worker --loglevel=info
celery -A src.celery_app beat --loglevel=info
``` 