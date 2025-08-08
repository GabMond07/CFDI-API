from fastapi import APIRouter, Request, Query, Depends, Response, HTTPException
from src.service.aggregation_service import AggregationService
from src.service.join_service import JoinService
from src.service.stats_service import StatsService
from src.service.operation_service import SetOperationService
from src.Models.visualize import CFDIFilter, JoinRequest, SetOperationRequest
from src.service.export_service import generate_report_from_data
from src.permission import require_permissions
from datetime import datetime
from typing import Optional
import logging
from datetime import timezone
from src.database import db  # Import the db object for database access

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/aggregate", dependencies=[Depends(require_permissions(["reports:generate"]))])
async def aggregate_data(
    request: Request,
    filters: CFDIFilter = Depends(),
    operation: str = Query(..., regex="^(sum|count|avg|min|max)$"),
    field: str = Query(..., regex="^(total|subtotal)$"),
    include_details: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000)
):
    """
    Procesa agregaciones básicas (sum, count, avg, min, max) sobre CFDI.
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    service = AggregationService(user_rfc)
    
    # Procesar los datos
    result = await service.aggregate_data(operation, field, filters, include_details, page, page_size)
    
    # Determinar cfdi_id
    cfdi_id = None
    if filters.folio:
        cfdi = await db.cfdi.find_first(where={"folio": filters.folio, "user_id": user_rfc})
        if cfdi:
            cfdi_id = cfdi.id
        else:
            logger.warning(f"Folio {filters.folio} no encontrado para RFC {user_rfc}")

    # Generar el reporte
    report_result = await generate_report_from_data(
        data=result,
        format_type=filters.format,
        user={"rfc": user_rfc},
        cfdi_id=cfdi_id,
        save_report=filters.save_report
    )

    logger.info(f"Agregación generada para RFC: {user_rfc} en formato {filters.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return Response(
        content=report_result["content"],
        media_type=report_result["content_type"],
        headers={"Content-Disposition": f"attachment; filename=aggregate.{filters.format}"}
    )

@router.post("/stats/central-tendency", dependencies=[Depends(require_permissions(["reports:generate"]))])
async def central_tendency(
    request: Request,
    filters: CFDIFilter = Depends(),
    field: str = Query(..., regex="^(total|subtotal)$")
):
    """
    Calcula medidas de tendencia central (promedio, mediana, moda).
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    service = StatsService(user_rfc)
    
    # Procesar los datos
    result = await service.central_tendency(field, filters)
    
    # Determinar cfdi_id
    cfdi_id = None
    if filters.folio:
        cfdi = await db.cfdi.find_first(where={"folio": filters.folio, "user_id": user_rfc})
        if cfdi:
            cfdi_id = cfdi.id
        else:
            logger.warning(f"Folio {filters.folio} no encontrado para RFC {user_rfc}")

    # Generar el reporte
    report_result = await generate_report_from_data(
        data=[result],  # Envolver en lista para consistencia
        format_type=filters.format,
        user={"rfc": user_rfc},
        cfdi_id=cfdi_id,
        save_report=filters.save_report
    )

    logger.info(f"Tendencia central generada para RFC: {user_rfc} en formato {filters.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return Response(
        content=report_result["content"],
        media_type=report_result["content_type"],
        headers={"Content-Disposition": f"attachment; filename=central_tendency.{filters.format}"}
    )

@router.post("/stats/basic", dependencies=[Depends(require_permissions(["reports:generate"]))])
async def basic_stats(
    request: Request,
    filters: CFDIFilter = Depends(),
    field: str = Query(..., regex="^(total|subtotal)$")
):
    """
    Calcula estadísticas básicas (rango, varianza, desviación estándar, coeficiente de variación).
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    service = StatsService(user_rfc)
    
    # Procesar los datos
    result = await service.basic_stats(field, filters)
    
    # Determinar cfdi_id
    cfdi_id = None
    if filters.folio:
        cfdi = await db.cfdi.find_first(where={"folio": filters.folio, "user_id": user_rfc})
        if cfdi:
            cfdi_id = cfdi.id
        else:
            logger.warning(f"Folio {filters.folio} no encontrado para RFC {user_rfc}")

    # Generar el reporte
    report_result = await generate_report_from_data(
        data=[result],  # Envolver en lista para consistencia
        format_type=filters.format,
        user={"rfc": user_rfc},
        cfdi_id=cfdi_id,
        save_report=filters.save_report
    )

    logger.info(f"Estadísticas básicas generadas para RFC: {user_rfc} en formato {filters.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return Response(
        content=report_result["content"],
        media_type=report_result["content_type"],
        headers={"Content-Disposition": f"attachment; filename=basic_stats.{filters.format}"}
    )

@router.post("/join", dependencies=[Depends(require_permissions(["join:execute"]))])
async def join_data(
    request: Request,
    join_request: JoinRequest,  # Cuerpo JSON explícito
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Número de registros por página")
):
    """
    Combina datos de múltiples tablas (joins virtuales).
    Acepta filtros en el campo 'filters' de JoinRequest.
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    Incluye paginación con page, page_size y total_pages.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    logger.info(f"Received request for /join: {join_request}, page: {page}, page_size: {page_size}")

    # Validar parámetros de paginación
    if page_size == 0:
        raise HTTPException(status_code=422, detail="page_size must be greater than 0")

    service = JoinService(user_rfc)
    
    # Procesar los datos con paginación
    try:
        result = await service.join_data(join_request, page, page_size)
    except ValueError as e:
        logger.error(f"Invalid join request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in join_data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    logger.info(f"Join personalizado generado para RFC: {user_rfc} en formato {join_request.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return {
        "content": result["content"],
        "content_type": result["content_type"],
        "report_id": result["report_id"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"]
    }

@router.post("/join/predefined", dependencies=[Depends(require_permissions(["join:execute"]))])
async def predefined_join(
    request: Request,
    join_id: int = Query(..., description="ID de la consulta predefinida"),
    filters: CFDIFilter = Depends(),
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Número de registros por página")
):
    """
    Ejecuta una consulta predefinida de join.
    Acepta filtros en el cuerpo JSON (CFDIFilter).
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    Incluye paginación con page, page_size y total_pages.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    logger.info(f"Received request for /join/predefined: join_id={join_id}, filters={filters}, page={page}, page_size={page_size}")

    # Validar parámetros de paginación
    if page_size == 0:
        raise HTTPException(status_code=422, detail="page_size must be greater than 0")

    service = JoinService(user_rfc)
    
    # Procesar la consulta predefinida con paginación
    try:
        result = await service.execute_predefined_join(join_id, filters, page, page_size)
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in predefined_join: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    logger.info(f"Join predefinido {join_id} generado para RFC: {user_rfc} en formato {filters.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return {
        "content": result["content"],
        "content_type": result["content_type"],
        "report_id": result["report_id"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"]
    }

@router.get("/join/predefined", dependencies=[Depends(require_permissions(["join:execute"]))])
async def list_predefined_joins(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of items per page")
):
    """
    Lista todas las consultas predefinidas disponibles con paginación.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    service = JoinService(user_rfc)
    result = service.get_predefined_joins(page, page_size)
    logger.info(f"Lista de consultas predefinidas generada para RFC: {user_rfc} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return result

@router.post("/set_operation", dependencies=[Depends(require_permissions(["sets_execute"]))])
async def set_operation(
    request: Request,
    set_request: SetOperationRequest,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000)
):
    """
    Realiza operaciones de conjuntos (union, intersection) sobre datos CFDI.
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    logger.info(f"Received request for /set_operation: {set_request}, page: {page}, page_size: {page_size}")
    service = SetOperationService(user_rfc)
    
    try:
        # Procesar los datos
        result = await service.set_operation(set_request, page, page_size)
        
        # Determinar cfdi_id
        cfdi_id = None
        if set_request.left_filters.folio:
            cfdi = await db.cfdi.find_first(where={"folio": set_request.left_filters.folio, "user_id": user_rfc})
            if cfdi:
                cfdi_id = cfdi.id
            else:
                logger.warning(f"Folio {set_request.left_filters.folio} no encontrado para RFC {user_rfc}")
        elif set_request.right_filters.folio:
            cfdi = await db.cfdi.find_first(where={"folio": set_request.right_filters.folio, "user_id": user_rfc})
            if cfdi:
                cfdi_id = cfdi.id
            else:
                logger.warning(f"Folio {set_request.right_filters.folio} no encontrado para RFC {user_rfc}")

        # Generar el reporte
        report_result = await generate_report_from_data(
            data=result,
            format_type=set_request.format,
            user={"rfc": user_rfc},
            cfdi_id=cfdi_id,
            save_report=set_request.save_report
        )

        logger.info(f"Operación de conjuntos generada para RFC: {user_rfc} en formato {set_request.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
        return Response(
            content=report_result["content"],
            media_type=report_result["content_type"],
            headers={"Content-Disposition": f"attachment; filename=set_operation.{set_request.format}"}
        )
    except Exception as e:
        logger.error(f"Error in set_operation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")