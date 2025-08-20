from fastapi import APIRouter, Request, Query, Depends, Response, HTTPException, BackgroundTasks
from src.service.operation.join_service import JoinService
from src.Models.operation.common import CFDIFilter
from src.service.operation.export_service import generate_report_from_data
# from src.service.notification_service import NotificationService
from src.permission import require_permissions
from datetime import datetime, timezone
from src.database import db
import logging

router = APIRouter(tags=["Data processing and transformation"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/join/predefined", dependencies=[Depends(require_permissions(["join:execute"]))])
async def predefined_join(
    request: Request,
    join_id: int = Query(..., description="ID de la consulta predefinida"),
    filters: CFDIFilter = Depends(),
    page: int = Query(1, ge=1, description="Número de página (comienza en 1)"),
    page_size: int = Query(100, ge=1, le=1000, description="Número de registros por página"),
    background_tasks: BackgroundTasks = None
):
    """
    Ejecuta una consulta predefinida de join.
    Devuelve el resultado en el formato especificado (json, xml, csv, excel, pdf).
    Opcionalmente guarda el resultado como un reporte con metadatos adicionales y notifica via webhook.
    Incluye paginación con page, page_size y total_pages.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    logger.info(f"Received request for /join/predefined: join_id={join_id}, filters={filters}, page={page}, page_size={page_size}")

    # Validar parámetros de paginación
    if page_size == 0:
        raise HTTPException(status_code=422, detail="page_size must be greater than 0")

    service = JoinService(user_rfc)
    
    try:
        # Procesar la consulta predefinida con paginación
        result = await service.execute_predefined_join(join_id, filters, page, page_size)

        # Serializar filtros como diccionario para el campo filters
        filters_dict = filters.dict(exclude_unset=True)
        if filters_dict.get("start_date"):
            filters_dict["start_date"] = filters_dict["start_date"].isoformat()
        if filters_dict.get("end_date"):
            filters_dict["end_date"] = filters_dict["end_date"].isoformat()

        # Determinar cfdi_id
        cfdi_id = None
        if filters.folio:
            cfdi = await db.cfdi.find_first(where={"folio": filters.folio, "user_id": user_rfc})
            if cfdi:
                cfdi_id = cfdi.id
            else:
                logger.warning(f"Folio {filters.folio} no encontrado para RFC {user_rfc}")
                raise HTTPException(status_code=404, detail=f"Folio {filters.folio} not found")

        # Generar el reporte
        report_result = await generate_report_from_data(
            data=[result["content"]] if isinstance(result["content"], dict) else result["content"],
            format_type=filters.format,
            user={"rfc": user_rfc},
            cfdi_id=cfdi_id,
            save_report=filters.save_report,
            name=filters.name,
            description=filters.description,
            filters=filters_dict,
            operation="predefined_join"
        )

        # Enviar notificación via webhook si se guarda el reporte (RF12)
        # if filters.save_report and report_result["report_id"]:
        #     background_tasks.add_task(
        #         NotificationService.notify_webhook,
        #         user_rfc=user_rfc,
        #         event_type="analysis_ready",
        #         payload={"report_id": report_result["report_id"], "format": filters.format}
        #     )

        logger.info(
            f"Join predefinido {join_id} generado para RFC: {user_rfc} en formato {filters.format}, "
            f"guardado: {filters.save_report}, nombre: {filters.name}, "
            f"descripción: {filters.description}, operación: predefined_join, "
            f"en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos"
        )

        return {
            "content": report_result["content"],
            "content_type": report_result["content_type"],
            "report_id": report_result["report_id"],
            "page": result["page"],
            "page_size": result["page_size"],
            "total_pages": result["total_pages"]
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en join predefinido {join_id} para RFC {user_rfc}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process predefined join: {str(e)}")

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