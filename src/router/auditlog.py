from fastapi import APIRouter, Depends
from src.Models.FiltroAuditLog import FiltroAuditLog
from src.service.auditlog_service import consultar_logs
from src.auth import get_current_user

router = APIRouter()

@router.get("/logs")
async def listar_logs(
    filtros: FiltroAuditLog = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_logs(filtros, user_rfc=usuario["rfc"])
