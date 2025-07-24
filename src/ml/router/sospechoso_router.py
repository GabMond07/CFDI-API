from fastapi import APIRouter
from src.event_bus_publisher import publish_event

router = APIRouter()

@router.get("/cfdi/prediccion-sospechoso")
async def clasificar_todos_cfdis():
    payload = {}
    await publish_event("prediccion_sospechoso", payload)
    return {"mensaje": "Evento publicado correctamente. El proceso se ejecutará en segundo plano."}
