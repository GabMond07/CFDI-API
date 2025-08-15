from fastapi import APIRouter, Request, Query, Depends, Response, HTTPException, BackgroundTasks
from src.service.operation.aggregation_service import AggregationService
from src.Models.operation.common import CFDIFilter
from src.service.operation.export_service import generate_report_from_data
# from src.service.notification_service import NotificationService
from src.permission import require_permissions
from datetime import datetime, timezone
from src.database import db 
import logging

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
    page_size: int = Query(100, ge=1, le=1000),
    background_tasks: BackgroundTasks = None
):
    """
    Procesa agregaciones básicas (sum, count, avg, min, max) sobre CFDI.
    Devuelve el resultado en el formato especificado (json, xml, csv, excel, pdf).
    Opcionalmente guarda el resultado como un reporte con metadatos adicionales y notifica via webhook.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    service = AggregationService(user_rfc)
    
    try:
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
                raise HTTPException(status_code=404, detail=f"Folio {filters.folio} not found")

        # Serializar filtros como diccionario para el campo filters
        filters_dict = filters.dict(exclude_unset=True)
        if filters_dict.get("start_date"):
            filters_dict["start_date"] = filters_dict["start_date"].isoformat()
        if filters_dict.get("end_date"):
            filters_dict["end_date"] = filters_dict["end_date"].isoformat()

        # Generar el reporte
        report_result = await generate_report_from_data(
            data=[result] if isinstance(result, dict) else result,  # Envolver en lista si es necesario
            format_type=filters.format,
            user={"rfc": user_rfc},
            cfdi_id=cfdi_id,
            save_report=filters.save_report,
            name=filters.name,
            description=filters.description,
            filters=filters_dict,
            operation="aggregate"
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
            f"Agregación generada para RFC: {user_rfc} en formato {filters.format}, "
            f"guardado: {filters.save_report}, nombre: {filters.name}, "
            f"descripción: {filters.description}, operación: aggregate, "
            f"en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos"
        )
        
        return Response(
            content=report_result["content"],
            media_type=report_result["content_type"],
            headers={"Content-Disposition": f"attachment; filename=aggregate.{filters.format}"}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en agregación para RFC {user_rfc}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process aggregation: {str(e)}")