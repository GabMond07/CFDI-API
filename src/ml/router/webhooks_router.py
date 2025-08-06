from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["Webhooks"])

# Base de datos temporal (puedes reemplazarla con tu DB real)
webhook_results_db = []


class WebhookResult(BaseModel):
    status: str  # "completed" o "failed"
    data: list[dict] | None  # Resultados de los CFDI
    error: str | None  # Mensaje de error (si falló)


@router.post("/webhook/cfdi-results")
async def receive_cfdi_results(
        result: WebhookResult,
        request: Request
):
    """Endpoint que recibirá los resultados de tu worker."""
    # Guarda los resultados en tu "DB temporal"
    webhook_results_db.append({
        "data": result.dict(),
        "received_at": datetime.now(),
        "client_ip": request.client.host
    })

    print(f"📬 Webhook recibido! Estado: {result.status}")
    return {"message": "Resultados recibidos con éxito"}


@router.get("/webhook/last-result")
async def get_last_result():
    """Opcional: Endpoint para ver el último resultado recibido."""
    if not webhook_results_db:
        raise HTTPException(status_code=404, detail="No hay resultados aún")
    return webhook_results_db[-1]