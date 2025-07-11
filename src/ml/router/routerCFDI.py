from fastapi import APIRouter
from src.ml.service.serviceCFDI import clasificar_tipo_cfdi

router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.get("/clasificar")
async def ejecutar_modelo():
    return await clasificar_tipo_cfdi()
