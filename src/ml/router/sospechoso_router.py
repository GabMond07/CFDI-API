from fastapi import APIRouter
from src.ml.service.predictor import clasificar_todos_cfdis_service

router = APIRouter()

@router.get("/cfdi/prediccion-sospechoso")
async def clasificar_todos_cfdis():
    resultado = await clasificar_todos_cfdis_service()
    return resultado
