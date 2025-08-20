from fastapi import APIRouter, Depends
from src.Models.filtro_payment import FiltroPayment
from src.service.payment_service import consultar_pagos
from src.auth import get_current_user

router = APIRouter(tags=["Data Query and Filtering"])

@router.get("/pagos")
async def listar_pagos(
    filtros: FiltroPayment = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_pagos(filtros, user_rfc=usuario["rfc"])
