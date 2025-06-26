from fastapi import APIRouter, Depends
from src.Models.FiltroBatchJob import FiltroBatchJob
from src.service.batchjob_service import consultar_batchjobs
from src.auth import get_current_user

router = APIRouter()

@router.get("/batchjobs")
async def listar_batchjobs(
    filtros: FiltroBatchJob = Depends(),
    usuario = Depends(get_current_user)
):
    return await consultar_batchjobs(filtros, user_rfc=usuario["rfc"])
