from fastapi import APIRouter, Depends
from src.Models.FiltroReport import FiltroReport
from src.service.report_service import consultar_reportes
from src.auth import get_current_user

router = APIRouter()

@router.get("/reportes")
async def listar_reportes(
    filtros: FiltroReport = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_reportes(filtros, user_rfc=usuario["rfc"])
