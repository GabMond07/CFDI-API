from fastapi import APIRouter, Depends
from src.Models.filtro_tax import FiltroTax
from src.service.tax_service import consultar_taxes
from src.auth import get_current_user

router = APIRouter()

@router.get("/impuestos")
async def listar_impuestos(
    filtros: FiltroTax = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_taxes(filtros, user_rfc=usuario["rfc"])
