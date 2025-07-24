from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import JSONResponse
from src.service.visualize_service import CFDIProcessor
from src.Models.visualize import CFDIFilter 

router = APIRouter()

@router.post("/cfdi/visualize")
async def visualize_cfdi(
    request: Request,
    filters: CFDIFilter = Depends(),
    aggregation: str = Query("sum", regex="^(sum|count|avg|min|max)$"),
    include_details: bool = Query(False),
    page: int = Query(1, ge=1),  # Número de página, comenzando en 1
    page_size: int = Query(100, ge=1, le=1000)  # Registros por página
):
    """
    Procesa datos de CFDI con filtros, agregaciones y detalles opcionales.
    """
    user_rfc = request.state.user["sub"]  # Obtenemos el RFC del usuario autenticado
    processor = CFDIProcessor(user_rfc)
    result = await processor.process_data(filters, aggregation, include_details, page, page_size)
    return JSONResponse(content=result)