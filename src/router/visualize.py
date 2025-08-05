from fastapi import APIRouter, Request, Query, Depends, Response
from src.service.visualize_service import CFDIProcessor
from src.Models.visualize import CFDIFilter
from src.permission import require_permissions
from src.service.export_service import generate_report_from_data
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/visualize", dependencies=[Depends(require_permissions(["read_cfdis"]))])
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
    Devuelve el resultado en el formato especificado (json, xml, csv, excel).
    Opcionalmente guarda el resultado como un reporte.
    """
    start_time = datetime.now(timezone.utc)
    user_rfc = request.state.user["sub"]  # Obtenemos el RFC del usuario autenticado
    processor = CFDIProcessor(user_rfc)
    
    # Procesar los datos con CFDIProcessor
    result = await processor.process_data(filters, aggregation, include_details, page, page_size)
    
    # Generar el reporte en el formato solicitado
    report_result = await generate_report_from_data(
        data=result,
        format_type=filters.format,
        user={"rfc": user_rfc},
        cfdi_id=int(filters.folio) if filters.folio else None,  # Convertir folio a int si existe
        save_report=filters.save_report
    )

    logger.info(f"Visualización generada para RFC: {user_rfc} en formato {filters.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return Response(
        content=report_result["content"],
        media_type=report_result["content_type"],
        headers={"Content-Disposition": f"attachment; filename=visualization.{filters.format}"}
    )