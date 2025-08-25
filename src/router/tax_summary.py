from fastapi import APIRouter, Depends
from src.service.tax_summary_service import resumen_impuestos_por_usuario
from src.auth import get_current_user

router = APIRouter(tags=["Data Query and Filtering"])

@router.get("/impuestos/resumen")
async def resumen_impuestos(usuario = Depends(get_current_user)):
    return await resumen_impuestos_por_usuario(usuario["rfc"])
