from fastapi import APIRouter, Depends
from src.Models.filtro_concept import FiltroConcept
from src.service.concept_service import consultar_conceptos
from src.auth import get_current_user

router = APIRouter()

@router.get("/conceptos")
async def listar_conceptos(
    filtros: FiltroConcept = Depends(),
    usuario = Depends(get_current_user)
):
        return await consultar_conceptos(filtros, user_rfc=usuario["rfc"])
