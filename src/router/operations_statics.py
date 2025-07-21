from fastapi import APIRouter, Request, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from src.service.aggregation_service import AggregationService
from src.service.join_service import JoinService
from src.service.stats_service import StatsService
from src.service.operation_service import SetOperationService
from src.Models.visualize import CFDIFilter, JoinRequest, SetOperationRequest, ScriptRequest, OperationType
from datetime import datetime
from typing import Optional
import logging

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/aggregate")
async def aggregate_data(
    request: Request,
    operation: str = Query(..., regex="^(sum|count|avg|min|max)$"),
    field: str = Query(..., regex="^(total|subtotal)$"),
    include_details: bool = Query(False),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None),
    receiver_id: Optional[int] = Query(None),
    currency: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    payment_form: Optional[str] = Query(None),
    cfdi_use: Optional[str] = Query(None),
    export_status: Optional[str] = Query(None),
    min_total: Optional[float] = Query(None),
    max_total: Optional[float] = Query(None),
    page: int = Query(1, ge=1),  # Page number, starting at 1
    page_size: int = Query(100, ge=1, le=1000)  # Records per page
):
    """
    Procesa agregaciones básicas (sum, count, avg, min, max) sobre CFDI.
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id,
        receiver_id=receiver_id,
        currency=currency,
        payment_method=payment_method,
        payment_form=payment_form,
        cfdi_use=cfdi_use,
        export_status=export_status,
        min_total=min_total,
        max_total=max_total
    )
    service = AggregationService(user_rfc)
    result = await service.aggregate_data(operation, field, filters, include_details, page, page_size)
    return JSONResponse(content=result)

@router.post("/stats/central-tendency")
async def central_tendency(
    request: Request,
    field: str = Query(..., regex="^(total|subtotal)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None),
    receiver_id: Optional[int] = Query(None),
    currency: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    payment_form: Optional[str] = Query(None),
    cfdi_use: Optional[str] = Query(None),
    export_status: Optional[str] = Query(None),
    min_total: Optional[float] = Query(None),
    max_total: Optional[float] = Query(None)
):
    """
    Calcula medidas de tendencia central (promedio, mediana, moda).
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id,
        receiver_id=receiver_id,
        currency=currency,
        payment_method=payment_method,
        payment_form=payment_form,
        cfdi_use=cfdi_use,
        export_status=export_status,
        min_total=min_total,
        max_total=max_total
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
    type: Optional[str] = Query(None),
    serie: Optional[str] = Query(None),
    folio: Optional[str] = Query(None),
    issuer_id: Optional[str] = Query(None),
    receiver_id: Optional[int] = Query(None),
    currency: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    payment_form: Optional[str] = Query(None),
    cfdi_use: Optional[str] = Query(None),
    export_status: Optional[str] = Query(None),
    min_total: Optional[float] = Query(None),
    max_total: Optional[float] = Query(None)
):
    """
    Calcula estadísticas básicas (rango, varianza, desviación estándar, coeficiente de variación).
    """
    user_rfc = request.state.user["sub"]
    filters = CFDIFilter(
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
        type=type,
        serie=serie,
        folio=folio,
        issuer_id=issuer_id,
        receiver_id=receiver_id,
        currency=currency,
        payment_method=payment_method,
        payment_form=payment_form,
        cfdi_use=cfdi_use,
        export_status=export_status,
        min_total=min_total,
        max_total=max_total
    )
    service = StatsService(user_rfc)
    result = await service.basic_stats(field, filters)
    return JSONResponse(content=result)

@router.post("/join")
async def join_data(
    request: Request,
    join_request: JoinRequest = Depends(),
    page: int = Query(1, ge=1),  # Page number, starting at 1
    page_size: int = Query(100, ge=1, le=1000)  # Records per page
):
    """
    Combina datos de múltiples tablas (joins virtuales).
    """
    user_rfc = request.state.user["sub"]
    logger.info(f"Received request for /join: {join_request}, page: {page}, page_size: {page_size}")
    service = JoinService(user_rfc)
    result = await service.join_data(join_request, page, page_size)
    return JSONResponse(content={"items": result})

@router.post("/set_operation")
async def set_operation(
    request: Request,
    set_request: SetOperationRequest,
    page: int = Query(1, ge=1),  # Page number, starting at 1
    page_size: int = Query(100, ge=1, le=1000)  # Records per page
):
    """
    Realiza operaciones de conjuntos (union, intersection) sobre datos CFDI.
    """
    try:
        user_rfc = request.state.user["sub"]
        logger.info(f"Received request for /api/v1/cfdi/set_operation: {set_request}, page: {page}, page_size: {page_size}")
        service = SetOperationService(user_rfc)
        result = await service.set_operation(set_request, page, page_size)
        return JSONResponse(content={"result": result})
    except Exception as e:
        logger.error(f"Error in set_operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")