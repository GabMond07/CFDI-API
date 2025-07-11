from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from src.service.aggregation_service import AggregationService
from src.service.join_service import JoinService
from src.service.stats_service import StatsService
from src.service.operation_service import SetOperationService
from src.service.script_service import ScriptService
from src.Models.visualize import CFDIFilter, JoinRequest, SetOperationRequest, ScriptRequest
from datetime import datetime
from typing import Optional

import logging

logger = logging.getLogger(__name__)
router = APIRouter()

router = APIRouter()

@router.post("/aggregate")
async def aggregate_data(
    request: Request,
    operation: str = Query(..., regex="^(sum|count|avg|min|max)$"),
    field: str = Query(..., regex="^(total|subtotal)$"),
    include_details: bool = Query(False),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None)
):
    """
    Procesa agregaciones básicas (sum, count, avg, min, max) sobre CFDI.
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        status=status,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id
    )
    service = AggregationService(user_rfc)
    result = await service.aggregate_data(operation, field, filters, include_details)
    return JSONResponse(content=result)

@router.post("/stats/central-tendency")
async def central_tendency(
    request: Request,
    field: str = Query(..., regex="^(total|subtotal)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None)
):
    """
    Calcula medidas de tendencia central (promedio, mediana, moda).
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        status=status,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id
    )
    service = StatsService(user_rfc)
    result = await service.central_tendency(field, filters)
    return JSONResponse(content=result)

@router.post("/stats/basic")
async def basic_stats(
    request: Request,
    field: str = Query(..., regex="^(total|subtotal)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None)
):
    """
    Calcula estadísticas básicas (rango, varianza, desviación estándar, coeficiente de variación).
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        status=status,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id
    )
    service = StatsService(user_rfc)
    result = await service.basic_stats(field, filters)
    return JSONResponse(content=result)

@router.post("/join")
async def join_data(
    request: Request,
    join_request: JoinRequest = Depends()
):
    """
    Combina datos de múltiples tablas (joins virtuales).
    """
    user_rfc = request.state.user["sub"]
    service = JoinService(user_rfc)
    result = await service.join_data(join_request)
    return JSONResponse(content={"items": result})

@router.post("/sets/operation")
async def set_operation(
    request: Request,
    set_request: SetOperationRequest
):
    """
    RF08: Realiza operaciones de conjuntos sobre múltiples fuentes de datos CFDI.
    
    Permite combinar datos de múltiples consultas usando operaciones de unión e intersección.
    """
    try:
        user_rfc = request.state.user["sub"]
        logger.info(f"Set operation '{set_request.operation}' requested by user {user_rfc}")
        
        # Validar que haya suficientes fuentes para operaciones de conjunto
        if len(set_request.sources) < 2 and set_request.operation == OperationType.INTERSECTION:
            raise HTTPException(
                status_code=400,
                detail="Intersection operation requires at least 2 data sources"
            )
        
        # Ejecutar operación
        service = SetOperationService(user_rfc)
        result = await service.set_operation(set_request)
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in set_operation endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
@router.post("/scripts/execute")
async def execute_script(
    request: Request,
    script_request: ScriptRequest = Depends()
):
    """
    Placeholder para ejecutar scripts personalizados (Python, R, SQL). No implementado en la versión beta.
    """
    user_rfc = request.state.user["sub"]
    return JSONResponse(content={"message": "Script execution not implemented in beta"})

@router.post("/scripts/sql")
async def execute_sql(
    request: Request,
    query: str = Query(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None)
):
    """
    Ejecuta consultas SQL predefinidas sobre CFDI (versión beta).
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        status=status,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id
    )
    service = ScriptService(user_rfc)
    try:
        result = await service.execute_sql(query, filters)
        return JSONResponse(content={"result": result})
    except ValueError as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)