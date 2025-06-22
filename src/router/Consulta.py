from fastapi import APIRouter, Depends
from src.Models.Consulta import FiltroConsulta
from src.service.consulta_service import filtrar_cfdi
from src.router.obtener_filtros import obtener_filtros
from src.auth import get_current_user

router = APIRouter()

@router.get("/consulta")
async def consultar_datos(
    filtros: FiltroConsulta = Depends(),
    usuario = Depends(get_current_user)
):
        return await filtrar_cfdi(filtros, user_rfc=usuario["rfc"])
