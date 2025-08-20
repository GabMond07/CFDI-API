from fastapi import APIRouter, Request, Query, Depends, Response, HTTPException
from src.service.operation.stats_service import StatsService
from src.Models.operation.common import CFDIFilter
from src.service.operation.export_service import generate_report_from_data
from src.permission import require_permissions
from datetime import datetime, timezone
from src.database import db 
import logging

router = APIRouter(tags=["Data processing and transformation"])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/stats/central-tendency", dependencies=[Depends(require_permissions(["reports:generate"]))])
async def central_tendency(
    request: Request,
    filters: CFDIFilter = Depends(),
    field: str = Query(..., regex="^(total|subtotal)$")
):
    """
    Calcula medidas de tendencia central (promedio, mediana, moda).
    Devuelve el resultado en el formato especificado (json, xml, csv, excel, pdf).
    Opcionalmente guarda el resultado como un reporte con metadatos adicionales.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]
    service = StatsService(user_rfc)
    
    try:
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
            operation="central_tendency"
        )

        logger.info(
            f"Tendencia central generada para RFC: {user_rfc} en formato {filters.format}, "
            f"guardado: {filters.save_report}, nombre: {filters.name}, "
            f"descripción: {filters.description}, operación: central_tendency, "
            f"en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos"
        )
        
        return Response(
            content=report_result["content"],
            media_type=report_result["content_type"],
            headers={"Content-Disposition": f"attachment; filename=central_tendency.{filters.format}"}
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error en tendencia central para RFC {user_rfc}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process central tendency: {str(e)}")