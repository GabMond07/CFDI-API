from fastapi import APIRouter
from src.event_bus.publisher import publish_event
from pydantic import BaseModel

router = APIRouter()


class PredictionRequest(BaseModel):
    callback_url: str = "http://localhost:8000/webhook/cfdi-results"

@router.post("/cfdi/prediccion-sospechoso")
async def clasificar_todos_cfdis(request: PredictionRequest):
    """
    Inicia el procesamiento de CFDI y notificará al callback_url cuando termine
    """
    if not is_valid_url(request.callback_url):
        raise HTTPException(status_code=400, detail="URL de callback inválida")

    payload = {
        "callback_url": request.callback_url,
        "auth_token": generate_auth_token()  # Para seguridad
    }

    await publish_event("prediccion_sospechoso", payload)
    return {"status": "procesando", "callback_url": request.callback_url}


from fastapi import Header, HTTPException


# Función para verificar tokens (usar en el receptor del webhook)
def verify_webhook_token(authorization: str = Header(...)):
    scheme, token = authorization.split()
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=403, detail="Esquema de autenticación inválido")

    if not validate_token(token):  # Implementa tu lógica de validación
        raise HTTPException(status_code=403, detail="Token inválido o expirado")

    return token

