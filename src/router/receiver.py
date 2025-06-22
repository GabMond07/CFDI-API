from fastapi import APIRouter, Depends
from src.Models.filtro_receiver import FiltroReceiver
from src.service.receiver_service import consultar_receiver
from src.auth import get_current_user

router = APIRouter()

@router.get("/receptores")
async def listar_receptores(
    filtros: FiltroReceiver = Depends(),
    usuario = Depends(get_current_user)
):
        return await consultar_receiver(filtros, user_rfc=usuario["rfc"])
