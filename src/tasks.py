from celery import shared_task
from .auth import clean_expired_tokens
import asyncio

@shared_task
def clean_expired_tokens_task():
    """
    Tarea para limpiar tokens expirados de la lista negra.
    """
    asyncio.run(clean_expired_tokens())