from fastapi import APIRouter, Depends
from src.Models.filtro_cfdi_relation import FiltroCFDIRelation
from src.service.cfdi_relation_service import consultar_cfdi_relations
from src.auth import get_current_user

router = APIRouter()

@router.get("/cfdi-relaciones")
async def listar_cfdi_relaciones(
    filtros: FiltroCFDIRelation = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_cfdi_relations(filtros, user_rfc=usuario["rfc"])
