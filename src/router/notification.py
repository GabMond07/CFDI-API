from fastapi import APIRouter, Depends
from src.Models.FiltroNotification import FiltroNotification
from src.service.notification_service import consultar_notificaciones
from src.auth import get_current_user

router = APIRouter()

@router.get("/notificaciones")
async def listar_notificaciones(
    filtros: FiltroNotification = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_notificaciones(filtros, user_rfc=usuario["rfc"])
