from fastapi import APIRouter, Depends
from src.Models.filtro_issuer import FiltroIssuer
from src.service.issuer_service import consultar_issuer
from src.auth import get_current_user

router = APIRouter(tags=["Data Query and Filtering"])

@router.get("/emisores")
async def listar_emisores(
    filtros: FiltroIssuer = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_issuer(filtros, user_rfc=usuario["rfc"])
