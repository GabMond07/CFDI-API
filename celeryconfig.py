from celery.schedules import crontab

beat_schedule = {
    "clean-expired-tokens-every-hour": {
        "task": "src.tasks.clean_expired_tokens_task",
        "schedule": crontab(minute="*/1"),  # Ejecutar cada hora en punto
        },
    }