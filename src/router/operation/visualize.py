from fastapi import APIRouter, Request, Query, Depends, Response, HTTPException
from src.service.operation.visualize_service import CFDIProcessor
from src.Models.operation.common import CFDIFilter
from src.permission import require_permissions
from src.service.operation.export_service import generate_report_from_data
import logging
from datetime import datetime, timezone
from src.database import db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data processing and transformation"])

@router.post("/visualize", dependencies=[Depends(require_permissions(["reports:generate"]))])
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
    Devuelve el resultado en el formato especificado (json, xml, csv, excel, pdf).
    Opcionalmente guarda el resultado como un reporte con metadatos adicionales.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]  # Obtenemos el RFC del usuario autenticado
    processor = CFDIProcessor(user_rfc)
    
    try:
        # Procesar los datos con CFDIProcessor
        result = await processor.process_data(filters, aggregation, include_details, page, page_size)
        
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

        # Generar el reporte en el formato solicitado
        report_result = await generate_report_from_data(
            data=[result] if isinstance(result, dict) else result,  # Asegurar que data sea una lista
            format_type=filters.format,
            user={"rfc": user_rfc},
            cfdi_id=cfdi_id,
            save_report=filters.save_report,
            name=filters.name,
            description=filters.description,
            filters=filters_dict,
            operation="visualize"
        )

        logger.info(
            f"Visualización generada para RFC: {user_rfc} en formato {filters.format}, "
            f"guardado: {filters.save_report}, nombre: {filters.name}, "
            f"descripción: {filters.description}, operación: visualize, "
            f"en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos"
        )
        
        return Response(
            content=report_result["content"],
            media_type=report_result["content_type"],
            headers={"Content-Disposition": f"attachment; filename=visualization.{filters.format}"}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en visualización para RFC {user_rfc}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process visualization: {str(e)}")